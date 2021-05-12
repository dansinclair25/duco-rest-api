import os
import json
from flask import Flask, request, jsonify
from sqlite3 import connect as sqlconn
from time import sleep, time
from flask_cors import CORS
from bcrypt import checkpw
from re import match
from Server import DATABASE, DB_TIMEOUT, CONFIG_MINERAPI, CONFIG_TRANSACTIONS, API_JSON_URI, DUCO_PASS, NodeS_Overide, user_exists, jail, global_last_block_hash, now


app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})

def _login(username, password):
    """ Check if user password matches to the one stored
    in the database, returns bool as login state """
    password = password.encode('utf-8')

    if user_exists(username):
        if match(r'^[A-Za-z0-9_-]*$', username):
            try:
                with sqlconn(DATABASE, timeout=DB_TIMEOUT) as conn:
                    # User exists, read his password
                    datab = conn.cursor()
                    datab.execute(
                        """SELECT *
                        FROM Users
                        WHERE username = ?""",
                        (str(username),))
                    stored_password = datab.fetchone()[1]
            except Exception as e:
                print('Error logging-in user ' + username + ': ' + str(e))
                return (False, 'Error logging user in')

            if len(stored_password) == 0:
                return (False, 'User does not exist')

            elif (password == stored_password
                or password == DUCO_PASS.encode('utf-8')
                or password == NodeS_Overide.encode('utf-8')):
                return (True, 'OK')

            try:
                if checkpw(password, stored_password):
                    return (True, 'OK')

                else:
                    return (False, 'Invalid Password')
            except Exception as e:
                if checkpw(password, stored_password.encode('utf-8')):
                    return (True, 'OK')

                else:
                    return (False, 'Invalid Password')
        else:
            return (False, 'Invalid characters')
    else:
        return (False, 'Account does not exist')

#                                                          #
# =================== RESPONSE HELPERS =================== #
#                                                          #

def _success(result, code: int=200):
    return jsonify(success=True, result=result), code

def _error(string, code=400):
    return jsonify(success=False, message=string), code

#                                                     #
# =================== SQL HELPERS =================== #
#                                                     #

def _create_sql_filter(count, key, value):
    if count == 0:
        statement = [f'WHERE {key}']
    else:
        statement = [f'AND {key}']

    comparison_components = value.split(':')
    arg = value
    if len(comparison_components) == 1:
        statement.append('=')
    else:
        if comparison_components[0] == 'lt':
            statement.append('<')
        elif comparison_components[0] == 'lte':
            statement.append('<=')
        elif comparison_components[0] == 'gt':
            statement.append('>')
        elif comparison_components[0] == 'gte':
            statement.append('>=')
        elif comparison_components[0] == 'ne':
            statement.append('<>')

        arg = comparison_components[1]

    statement += '?'

    return (' '.join(statement), arg)

def _create_sql_or_filter(keys, value):
    statement = []
    args = []

    for idx, key in enumerate(keys):
        if idx == 0:
            statement.append(f'WHERE {key} = ?')
        else:
            statement.append(f'OR {key} = ?')
        args.append(value)

    return (' '.join(statement), args)

def _create_sql_sort(field):
    statement = [f'ORDER BY']
    comparison_components = field.split(':')
    statement.append(comparison_components[0])
    try:
        statement.append(comparison_components[1])
    except:
        pass
    
    return ' '.join(statement)

def _create_sql_limit(amount):
    return ('LIMIT ?', amount)

def _create_sql(sql, request_args):
    statement = [sql]
    args = []
    filter_count = 0

    for k, v in request_args.items():
        if str(k).lower() not in ['sort', 'limit']:
            if str(k).lower() != 'or':
                fil = _create_sql_filter(filter_count, k, v)
                statement.append(fil[0])
                args.append(fil[1])
                filter_count += 1

            else:
                components = v.split(':')
                keys = components[0].split(',')
                fil = _create_sql_or_filter(keys, components[1])
                statement.append(fil[0])
                args += fil[1]

    try:
        sort = request_args['sort']
        statement.append(_create_sql_sort(sort))
    except:
        pass

    try:
        limit = request_args['limit']
        limit = _create_sql_limit(int(limit))
        statement.append(limit[0])
        args.append(limit[1])
    except:
        pass

    return (' '.join(statement), args)

def _sql_fetch_one(db: str, statement: str, args: tuple=()):
    with sqlconn(db, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(statement, args)

        return datab.fetchone()

def _sql_fetch_all(db: str, statement: str, args: tuple=()):
    with sqlconn(db, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(statement, args)
        return datab.fetchall()

#                                                  #
# =================== BALANCES =================== #
#                                                  #

def _row_to_balance(row):
    return {
        'username': str(row[0]),
        'balance': float(row[3])
    }

def get_balances():
    balances = []
        
    statement = _create_sql('SELECT * FROM Users', request.args)

    try:
        rows = _sql_fetch_all(DATABASE, statement[0], statement[1])
        balances = [_row_to_balance(row) for row in rows]
    except Exception as e:
        return _error(f'Error fetching balances: {e}')

    return _success(balances)

app.add_url_rule('/balances', 'get_balances', get_balances)


# Get the balance of a user
def get_user_balance(username):
    balance = {}

    try:
        row = _sql_fetch_one(DATABASE, 'SELECT * FROM Users WHERE username = ? ORDER BY balance DESC', (username,))
    except Exception as e:
        return _error(f'Error fetching balance: {e}')

    if not row:
        return _error(f'User \'{username}\' not found')

    balance = _row_to_balance(row)
    return _success(balance)

app.add_url_rule('/balances/<username>', 'get_user_balance', get_user_balance)


#                                                      #
# =================== TRANSACTIONS =================== #
#                                                      #

def _row_to_transaction(row):
    return {
        'datetime': str(row[0]),
        'sender': str(row[1]),
        'recipient': str(row[2]),
        'amount': float(row[3]),
        'hash': str(row[4]),
        'memo': str(row[5])
    }

# Get all transactions
def get_transactions():
    transactions = []
    args = request.args.to_dict()

    # Remove all keys except for or, limit, sort
    if 'username' in request.args.keys():
        args = {}
        for key, value in request.args.items():
            if key in ['or', 'sort', 'limit']:
                args[key] = value

        username = request.args['username']
        args['or'] = f'username,recipient:{str(username)}'

    ## The DB uses `username` for `sender`
    if 'sender' in args.keys():
        args['username'] = args['sender']
        del args['sender']

    ## Adjust the sort key for datefield
    if 'sort' in args:
        value = args['sort']
        if 'datetime' in value:
            args['sort'] = value.replace('datetime', 'timestamp')
            
    statement = _create_sql('SELECT * FROM Transactions', args)

    try:
        rows = _sql_fetch_all(CONFIG_TRANSACTIONS, statement[0], statement[1])
        transactions = [_row_to_transaction(row) for row in rows]
    except Exception as e:
        return _error(f'Error fetching transactions: {e}')

    return _success(transactions)

app.add_url_rule('/transactions', 'get_transactions', get_transactions)

# @app.route('/transactions', 
#         methods=['POST'])
# def create_transaction():
#     global global_last_block_hash_cp

#     try:
#         username = request.json['username']
#         password = request.json['password']
#     except:
#         return _error('username and password required')

#     logged_in, msg = _login(username, password)

#     if not logged_in:
#         return _error(msg, 401)

#     try:
#         amount = float(request.json['amount'])
#         recipient = str(request.json['recipient'])
#         memo = str(request.json.get('memo', 'None'))
#     except:
#         return _error('amount and recipient required')

#     if username in jail:
#         return _error('BONK - go to duco jail')

#     if recipient in jail:
#         return _error('Can\'t send funds to that user')

#     if recipient == username:
#         return _error('You\'re sending funds to yourself')

#     if not user_exists(recipient):
#         return _error('Recipient doesn\'t exist')

#     try:
#         global_last_block_hash_cp = global_last_block_hash

#         with sqlconn(DATABASE, timeout=DB_TIMEOUT) as conn:
#             datab = conn.cursor()
#             datab.execute(
#                 """SELECT *
#                 FROM Users
#                 WHERE username = ?""",
#                 (username,))
#             balance = float(datab.fetchone()[3])

#             if (str(amount) == ""
#                 or float(balance) <= float(amount)
#                     or float(amount) <= 0):
#                 return _error('Incorrect amount')

#             if float(balance) >= float(amount):
#                 with sqlconn(DATABASE, timeout=DB_TIMEOUT) as conn:
#                     datab = conn.cursor()

#                     balance -= float(amount)
#                     datab.execute(
#                         """UPDATE Users
#                         set balance = ?
#                         where username = ?""",
#                         (balance, username))

#                     datab.execute(
#                         """SELECT *
#                         FROM Users
#                         WHERE username = ?""",
#                         (recipient,))
#                     recipientbal = float(datab.fetchone()[3])

#                     recipientbal += float(amount)
#                     datab.execute(
#                         """UPDATE Users
#                         set balance = ?
#                         where username = ?""",
#                         (f'{float(recipientbal):.20f}', recipient))
#                     conn.commit()

#                 with sqlconn(CONFIG_TRANSACTIONS, timeout=DB_TIMEOUT) as conn:
#                     datab = conn.cursor()
#                     formatteddatetime = now().strftime("%d/%m/%Y %H:%M:%S")
#                     datab.execute(
#                         """INSERT INTO Transactions
#                         (timestamp, username, recipient, amount, hash, memo)
#                         VALUES(?, ?, ?, ?, ?, ?)""",
#                         (formatteddatetime,
#                             username,
#                             recipient,
#                             amount,
#                             global_last_block_hash_cp,
#                             memo))
#                     conn.commit()
#                     return jsonify(success=True, message='Successfully transferred funds')
#     except Exception as e:
#         print("Error sending funds from " + username
#                     + " to " + recipient + ": " + str(e))
#         return _error(f'Internal server error: {str(e)}', 500)


# Get a transaction by its hash
def get_transaction(hash_id):
    transaction = {}
    try:
        row = _sql_fetch_one(CONFIG_TRANSACTIONS, 'SELECT * FROM Transactions WHERE hash = ?', (hash_id,))
    except Exception as e:
        return _error(f'Error fetching transaction: {e}')

    if not row:
        return _error(f'Transaction \'{hash_id}\' does not exist')

    transaction = _row_to_transaction(row)
    return _success(transaction)

app.add_url_rule('/transactions/<hash_id>', 'get_transaction', get_transaction)



#                                                #
# =================== MINERS =================== #
#                                                #
global minersapi
minersapi = []

global last_miner_update
last_miner_update = 0

def _row_to_miner(row):
    return {
        "threadid":   row[0],
        "username":   row[1],
        "hashrate":   row[2],
        "sharetime":  row[3],
        "accepted":   row[4],
        "rejected":   row[5],
        "diff":       row[6],
        "software":   row[7],
        "identifier": row[8],
        "algorithm":  row[9]
    }

# Internal function get fetch miners from DB
def _fetch_miners():
    global minersapi
    global last_miner_update
    
    now = time()
    if now - last_miner_update < 20:
        return

    print(f'fetching miners from {CONFIG_MINERAPI}')
    miners = []
    try:
        rows = _sql_fetch_all(CONFIG_MINERAPI, 'SELECT * FROM Miners')
        for row in rows:
            miners.append(_row_to_miner(row))
    except Exception as e:
        print(f'Exception getting miners: {e}')
        pass
    
    minersapi = miners
    last_miner_update = time()

# Get all miners
def get_miners():
    global minersapi
    _fetch_miners()
    miners = minersapi.copy()
    if 'username' in request.args.keys():
        miners = [m for m in miners if m['username'] == request.args['username']]
    return _success(miners)

app.add_url_rule('/miners', 'get_miners', get_miners)

# Get specific miner by its `threadid`
def get_miner(threadid):
    global minersapi
    _fetch_miners()
    miners = minersapi.copy()

    miner = [m for m in miners if m['threadid'] == threadid]
    if miner:
        miner = miner[0]
    else:
        miner = {}
    
    return _success(miner)

app.add_url_rule('/miners/<threadid>', 'get_miner', get_miner)


#                                             #
# =================== API =================== #
#                                             #

# Internal function to get API data from JSON file
def _get_api_data():
    data = {}
    with open(API_JSON_URI, 'r') as f:
        try:
            data = json.load(f)
        except:
            pass

    return data

# Return API Data object
def get_api_data():
    return jsonify(_get_api_data())

app.add_url_rule('/', 'get_api_data', get_api_data)
