import os
import json
from flask import Flask, request, jsonify
from sqlite3 import connect as sqlconn
from time import sleep, time
from flask_cors import CORS
from bcrypt import checkpw
from re import match
from Server import DATABASE, DB_TIMEOUT, CONFIG_MINERAPI, CONFIG_TRANSACTIONS, API_JSON_URI, DUCO_PASS, NodeS_Overide, user_exists, jail, global_last_block_hash, now
    

# class RESTApp(Flask):

#     def __init__(self):
#         super(RESTApp, self).__init__(__name__)

#         cors = CORS(self, resources={r"*": {"origins": "*"}})



def create_app():
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

    def _error(string):
        return {'error': string}

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
                fil = _create_sql_filter(filter_count, k, v)
                statement.append(fil[0])
                args.append(fil[1])
                filter_count += 1

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

    #                                                  #
    # =================== BALANCES =================== #
    #                                                  #

    def _row_to_balance(row):
        return {
            'username': str(row[0]),
            'balance': float(row[3])
        }


    @app.route('/balances',
            methods=['GET'])
    def all_balances():
        balances = []
            
        sql_statement = _create_sql('SELECT * FROM Users', request.args)

        with sqlconn(DATABASE, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            
            datab.execute(sql_statement[0], sql_statement[1])
            for row in datab.fetchall():
                balances.append(_row_to_balance(row))

        return jsonify(balances)


    @app.route('/balances/<username>',
            methods=['GET'])
    def user_balances(username):
        balance = {}
        with sqlconn(DATABASE, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            datab.execute(
                """SELECT *
                FROM Users
                WHERE username = ?
                ORDER BY balance DESC""", (username,))
            row = datab.fetchone()
            if row:
                balance = _row_to_balance(row)

        return jsonify(balance)


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


    @app.route('/transactions',
            methods=['GET'])
    def all_transactions():
        transactions = []
        args = request.args.to_dict()

        ## The DB uses `username` for `sender`
        try:
            if args['sender']:
                args['username'] = args['sender']
                del args['sender']
        except:
            pass

        sql_statement = _create_sql('SELECT * FROM Transactions', args)

        print(sql_statement)
        with sqlconn(CONFIG_TRANSACTIONS, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            datab.execute(sql_statement[0], sql_statement[1])

            transactions = [_row_to_transaction(row) for row in datab.fetchall()]

        return jsonify(transactions)

    # @app.route('/transactions', methods=['POST'])
    # def create_transaction():
    #     try:
    #         username = request.json['username']
    #         password = request.json['password']
    #     except:
    #         return jsonify(_error('username and password required')), 400

    #     logged_in, msg = _login(username, password)

    #     if not logged_in:
    #         return jsonify(_error(msg)), 401

    #     try:
    #         amount = float(request.json['amount'])
    #         recipient = str(request.json['recipient'])
    #         memo = str(request.json.get('memo', 'None'))
    #     except:
    #         return jsonify(_error('amount and recipient required')), 400

    #     if username in jail:
    #         return jsonify(_error('BONK - go to duco jail')), 400

    #     if recipient in jail:
    #         return jsonify(_error('Can\'t send funds to that user')), 400

    #     if recipient == username:
    #         return jsonify(_error('You\'re sending funds to yourself')), 400

    #     if not user_exists(recipient):
    #         return jsonify(_error('Recipient doesn\'t exist')), 400

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
    #                 return jsonify(_error('Incorrect amount')), 400

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
    #                     return jsonify('Successfully transferred funds')
    #     except Exception as e:
    #         print("Error sending funds from " + username
    #                     + " to " + recipient + ": " + str(e))
    #         return jsonify(_error(f'Internal server error: {str(e)}'))


    @app.route('/transactions/<username>',
            methods=['GET'])
    def user_transactions(username):
        transactions = []
        with sqlconn(CONFIG_TRANSACTIONS, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            datab.execute(
                """SELECT * FROM Transactions 
                WHERE username = ? OR 
                recipient = ?""", (username, username))

            transactions = [_row_to_transaction(row) for row in datab.fetchall()]

        return jsonify(transactions)


    @app.route('/transactions/sender/<sender>/recipient/<recipient>',
            methods=['GET'])
    def transactions_from_to(sender, recipient):
        transactions = []
        with sqlconn(CONFIG_TRANSACTIONS, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            datab.execute(
                """SELECT * FROM Transactions 
                WHERE username = ? AND 
                recipient = ?""", (sender, recipient))

            transactions = [_row_to_transaction(row) for row in datab.fetchall()]

        return jsonify(transactions)


    @app.route('/transactions/<key>/<username>',
            methods=['GET'])
    def transactions_from(key, username):
        transactions = []

        if key in ['sender', 'recipient']:
            db_key = 'username' if key == 'sender' else 'recipient'
            with sqlconn(CONFIG_TRANSACTIONS, timeout=DB_TIMEOUT) as conn:
                datab = conn.cursor()
                datab.execute(
                    'SELECT * FROM Transactions WHERE '
                    + db_key
                    + '= ?', (username,))

                transactions = [_row_to_transaction(
                    row) for row in datab.fetchall()]

        return jsonify(transactions)


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

    def _fetch_miners():
        global minersapi
        global last_miner_update
        
        now = time()
        if now - last_miner_update < 20:
            return

        print(f'fetching miners from {CONFIG_MINERAPI}')
        miners = []
        with sqlconn(CONFIG_MINERAPI, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            datab.execute(
                """SELECT *
                FROM Miners""")
            """ Not sure if this is the best way to do this """
            for row in datab.fetchall():
                miners.append(_row_to_miner(row))
        
        minersapi = miners
        last_miner_update = time()

    @app.route('/miners',
            methods=['GET'])
    def all_miners():
        global minersapi
        _fetch_miners()
        miners = minersapi.copy()
        if 'username' in request.args.keys():
            miners = [m for m in miners if m['username'] == request.args['username']]
        return jsonify(miners)


    @app.route('/miners/<username>',
            methods=['GET'])
    def user_miners(username):
        global minersapi
        _fetch_miners()
        miners = minersapi.copy()

        return jsonify([m for m in miners if m['username'] == username])


    #                                             #
    # =================== API =================== #
    #                                             #

    def _get_api_data():
        data = {}
        with open(API_JSON_URI, 'r') as f:
            try:
                data = json.load(f)
            except:
                pass

        return data


    @app.route('/',
            methods=['GET'])
    def get_api_data():
        return jsonify(_get_api_data())

    return app
