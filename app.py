import os
import json
import threading
from flask import Flask, request, jsonify
from sqlite3 import connect as sqlconn
from time import sleep
from flask_cors import CORS

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

def create_app():
    app = Flask(__name__)
    cors = CORS(app, resources={r"*": {"origins": "*"}})


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

    def _create_sql(sql, request_args):
        statement = [sql]
        args = []
        filter_count = 0
        for k, v in request_args.items():
            if str(k).lower() == 'sort':
                statement.append(_create_sql_sort(v))
            else:
                fil = _create_sql_filter(filter_count, k, v)
                statement.append(fil[0])
                args.append(fil[1])
                filter_count += 1

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

        with sqlconn(CRYPTO_DATABASE, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            
            datab.execute(sql_statement[0], sql_statement[1])
            for row in datab.fetchall():
                balances.append(_row_to_balance(row))

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
        args = request.args.to_dict()

        ## The DB uses `username` for `sender`
        if args['sender']:
            args['username'] = args['sender']
            del args['sender']

        sql_statement = _create_sql('SELECT * FROM Transactions', args)

        with sqlconn(TRANSACTIONS_DATABASE, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            datab.execute(sql_statement[0], sql_statement[1])

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
    global minersapi
    minersapi = []

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
        while True:
            print(f'fetching miners from {MINERS_DATABASE}')
            miners = []
            with sqlconn(MINERS_DATABASE, timeout=DB_TIMEOUT) as conn:
                datab = conn.cursor()
                datab.execute(
                    """SELECT *
                    FROM Miners""")
                """ Not sure if this is the best way to do this """
                for row in datab.fetchall():
                    miners.append(_row_to_miner(row))
            
            minersapi = miners
            sleep(20)

    @app.route('/miners',
            methods=['GET'])
    def all_miners():
        global minersapi
        miners = minersapi.copy()
        return jsonify(miners)


    @app.route('/miners/<username>',
            methods=['GET'])
    def user_miners(username):
        global minersapi
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

    threading.Thread(target=_fetch_miners).start()

    return app

app = create_app()
