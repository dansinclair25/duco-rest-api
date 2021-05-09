import os
import json
from flask import Flask, request, jsonify
from sqlite3 import connect as sqlconn

try:
    import Server
    DB_TIMEOUT = Server.DB_TIMEOUT
    CRYPTO_DATABASE = Server.DATABASE
    TRANSACTIONS_DATABASE = Server.CONFIG_TRANSACTIONS
    API_JSON_URI = 'api.json'
    MINERS_DATABASE = Server.CONFIG_MINERAPI

except:
    DB_TIMEOUT = 10
    CONFIG_BASE_DIR = "../duco-rest-api-config"
    CRYPTO_DATABASE = os.path.join(CONFIG_BASE_DIR, 'crypto_database.db')
    TRANSACTIONS_DATABASE = os.path.join(CONFIG_BASE_DIR, "transactions.db")
    API_JSON_URI = os.path.join(CONFIG_BASE_DIR, 'api.json')
    MINERS_DATABASE = os.path.join(CONFIG_BASE_DIR, 'minerapi.db')

app = Flask(__name__)


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


@app.route('/balances/<username>',
           methods=['GET'])
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


@app.route('/transactions',
           methods=['GET'])
def all_transactions():
    transactions = []
    with sqlconn(TRANSACTIONS_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute("SELECT * FROM Transactions")

        transactions = [_row_to_transaction(row) for row in datab.fetchall()]

    return jsonify(transactions)


@app.route('/transactions/<username>',
           methods=['GET'])
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


@app.route('/transactions/sender/<sender>/recipient/<recipient>',
           methods=['GET'])
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


@app.route('/transactions/<key>/<username>',
           methods=['GET'])
def transactions_from(key, username):
    transactions = []

    if key in ['sender', 'recipient']:
        db_key = 'username' if key == 'sender' else 'recipient'
        with sqlconn(TRANSACTIONS_DATABASE, timeout=DB_TIMEOUT) as conn:
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

@app.route('/miners',
           methods=['GET'])
def all_miners():
    miners = []
    with sqlconn(MINERS_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(
            """SELECT *
            FROM Miners""")
        """ Not sure if this is the best way to do this """
        for row in datab.fetchall():
            miners.append(_row_to_miner(row))

    return jsonify(miners)


@app.route('/miners/<username>',
           methods=['GET'])
def user_miners(username):
    miners = []
    with sqlconn(MINERS_DATABASE, timeout=DB_TIMEOUT) as conn:
        datab = conn.cursor()
        datab.execute(
            """SELECT *
            FROM Miners
            WHERE username = ?""", (username,))
        """ Not sure if this is the best way to do this """
        for row in datab.fetchall():
            miners.append(_row_to_miner(row))

    return jsonify(miners)


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


@app.route('/api',
           methods=['GET'])
def get_api_data():
    return jsonify(_get_api_data())


if __name__ == '__main__':
    app.run(host='0.0.0.0')
