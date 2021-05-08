import os, json
from flask import Flask, request, jsonify
from sqlite3 import connect as sqlconn

try:
    import Server
    DB_TIMEOUT = Server.DB_TIMEOUT
    CRYPTO_DATABASE = Server.DATABASE
    TRANSACTIONS_DATABASE = Server.CONFIG_TRANSACTIONS
    MINERS = Server.minerapi.copy()
    API_JSON_URI = 'api.json'

except:
    DB_TIMEOUT = 10
    CONFIG_BASE_DIR = "../duco-rest-api-config"
    CRYPTO_DATABASE = os.path.join(CONFIG_BASE_DIR, 'crypto_database.db')
    TRANSACTIONS_DATABASE = os.path.join(CONFIG_BASE_DIR, "transactions.db")
    with open(os.path.join(CONFIG_BASE_DIR, 'miners.json'), 'r') as f:
        MINERS = json.load(f)
    API_JSON_URI = os.path.join(CONFIG_BASE_DIR, 'api.json')


app = Flask(__name__)



#                                                  #
# =================== BALANCES =================== #
#                                                  #

def _row_to_balance(row):
    return {
        'username': str(row[0]),
        'balance': float(row[3])
    }

@app.route('/balances', methods=['GET'])
def all_balances():
    balances = []
    with sqlconn(CRYPTO_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(
            """SELECT *
            FROM Users
            ORDER BY balance DESC""")
        for row in datab.fetchall():
            if float(row[3]) > 0:
                balances.append(_row_to_balance(row))
            else:
                # Stop when rest of the balances are just empty accounts
                break

    return jsonify(balances)

@app.route('/balances/<username>', methods=['GET'])
def user_balances(username):
    balance = {}
    with sqlconn(CRYPTO_DATABASE, timeout=DB_TIMEOUT) as conn:
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

@app.route('/transactions', methods=['GET'])
def all_transactions():
    transactions = []
    with sqlconn(TRANSACTIONS_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute("SELECT * FROM Transactions")
        
        transactions = [_row_to_transaction(row) for row in datab.fetchall()]
        
    return jsonify(transactions)

@app.route('/transactions/<username>', methods=['GET'])
def user_transactions(username):
    transactions = []
    with sqlconn(TRANSACTIONS_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(
            """SELECT * FROM Transactions 
            WHERE username = ? OR 
            recipient = ?""", (username, username))
        
        transactions = [_row_to_transaction(row) for row in datab.fetchall()]
        
    return jsonify(transactions)

@app.route('/transactions/<sender>/to/<recipient>', methods=['GET'])
def transactions_from_to(sender, recipient):
    transactions = []
    with sqlconn(TRANSACTIONS_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(
            """SELECT * FROM Transactions 
            WHERE username = ? AND 
            recipient = ?""", (sender, recipient))
        
        transactions = [_row_to_transaction(row) for row in datab.fetchall()]
        
    return jsonify(transactions)

@app.route('/transactions/to/<recipient>', methods=['GET'])
def transactions_to(recipient):
    transactions = []
    with sqlconn(TRANSACTIONS_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(
            """SELECT * FROM Transactions 
            WHERE recipient = ?""", (recipient,))
        
        transactions = [_row_to_transaction(row) for row in datab.fetchall()]
        
    return jsonify(transactions)

@app.route('/transactions/from/<sender>', methods=['GET'])
def transactions_from(sender):
    transactions = []
    with sqlconn(TRANSACTIONS_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(
            """SELECT * FROM Transactions 
            WHERE username = ?""", (sender,))
        
        transactions = [_row_to_transaction(row) for row in datab.fetchall()]
        
    return jsonify(transactions)



#                                                #
# =================== MINERS =================== #
#                                                #

def _get_miners():
    miners = []
    for k, v in MINERS.items():
        miner = {'id': k}
        for subK, subV in v.items():
            miner[str(subK).lower()] = subV

        miners.append(miner)
    
    return miners

@app.route('/miners', methods=['GET'])
def all_miners():
    return jsonify(_get_miners())


@app.route('/miners/<username>', methods=['GET'])
def user_miners(username):
    miners = [m for m in _get_miners() if m['user'] == username]
    return jsonify(miners)



#                                             #
# =================== API =================== #
#                                             #

def _get_api_data():
    with open(API_JSON_URI, 'r') as f:
        return json.load(f)

@app.route('/', methods=['GET'])
def get_api_data():
    return jsonify(_get_api_data())



if __name__ == '__main__':
    app.run()