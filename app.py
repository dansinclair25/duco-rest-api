import os
import sys
import json
from typing import Optional
from flask import Flask, request, jsonify
from sqlite3 import connect as sqlconn
from time import sleep, time
from bcrypt import checkpw
from re import match
from collections import OrderedDict
from operator import itemgetter
from Server import DATABASE, DB_TIMEOUT, CONFIG_MINERAPI, CONFIG_TRANSACTIONS, API_JSON_URI, DUCO_PASS, NodeS_Overide, user_exists, jail, global_last_block_hash, now, SAVE_TIME
from flask_caching import Cache

cache_conf = {
    "DEBUG": False,
    "CACHE_TYPE": "SpreadSASLMemcachedCache", # pylibmc module is required for "SpreadSASLMemcachedCache", if it cant be installed, "SimpleCache" can be used with a bit worse results
    "CACHE_DEFAULT_TIMEOUT": 3,
    "CACHE_IGNORE_ERRORS": True,
}

class DUCOApp(Flask):

    def __init__(self):
        super(DUCOApp, self).__init__(__name__)

        self.use_cache = True

        self.minersapi = []
        self.last_miner_update = 0

        self.use_cache = True

        self.minersapi = []
        self.last_miner_update = 0

        self.balances = []
        self.last_balances_update = 0

        self.transactions = []
        self.last_transactions_update = 0

        self.add_url_rule('/users/<username>', 'api_get_user_objects', self.api_get_user_objects)

        self.add_url_rule('/balances', 'api_get_balances', self.api_get_balances)
        self.add_url_rule('/balances/<username>', 'api_get_user_balance', self.api_get_user_balance)

        self.add_url_rule('/transactions', 'get_transactions', self.api_get_transactions)
        self.add_url_rule('/transactions/<hash_id>', 'get_transaction', self.api_get_transaction)

        self.add_url_rule('/miners', 'get_miners', self.api_get_miners)
        self.add_url_rule('/miners/<threadid>', 'get_miner', self.api_get_miner)

        self.add_url_rule('/statistics', 'get_api_data', self.get_api_data)


    #                                                          #
    # =================== RESPONSE HELPERS =================== #
    #                                                          #

    def _success(self, result, code: int=200):
        return jsonify(success=True, result=result), code

    def _error(self, string, code=400):
        return jsonify(success=False, message=string), code

    #                                                     #
    # =================== SQL HELPERS =================== #
    #                                                     #

    def _create_sql_filter(self, count, key, value):
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

    def _create_sql_or_filter(self, keys, value):
        statement = []
        args = []

        for idx, key in enumerate(keys):
            if idx == 0:
                statement.append(f'WHERE {key} = ?')
            else:
                statement.append(f'OR {key} = ?')
            args.append(value)

        return (' '.join(statement), args)

    def _create_sql_sort(self, field):
        statement = [f'ORDER BY']
        comparison_components = field.split(':')
        statement.append(comparison_components[0])
        try:
            statement.append(comparison_components[1])
        except:
            pass
        
        return ' '.join(statement)

    def _create_sql_limit(self, amount):
        return ('LIMIT ?', amount)

    def _create_sql(self, sql, request_args = {}):
        statement = [sql]
        args = []
        filter_count = 0

        for k, v in request_args.items():
            if str(k).lower() not in ['sort', 'limit']:
                if str(k).lower() != 'or':
                    fil = self._create_sql_filter(filter_count, k, v)
                    statement.append(fil[0])
                    args.append(fil[1])
                    filter_count += 1

                else:
                    components = v.split(':')
                    keys = components[0].split(',')
                    fil = self._create_sql_or_filter(keys, components[1])
                    statement.append(fil[0])
                    args += fil[1]

        try:
            sort = request_args['sort']
            statement.append(self._create_sql_sort(sort))
        except:
            pass

        try:
            limit = request_args['limit']
            limit = self._create_sql_limit(int(limit))
            statement.append(limit[0])
            args.append(limit[1])
        except:
            pass

        return (' '.join(statement), args)

    def _sql_fetch_one(self, db: str, statement: str, args: tuple=()):
        with sqlconn(db, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            datab.execute(statement, args)

            return datab.fetchone()

    def _sql_fetch_all(self, db: str, statement: str, args: tuple=()):
        rows=[]
        with sqlconn(db, timeout=DB_TIMEOUT) as conn:
            datab = conn.cursor()
            datab.execute(statement, args)
            rows = datab.fetchall()
            datab.close()
        conn.close()
        return rows
        
    #                                              #
    # =================== USER =================== #
    #                                              #

    def api_get_user_objects(self, username: str):
        miners = self._get_user_miners(username)
        
        try:
            transactions = self._get_user_transactions(username)
        except:
            transactions = []

        try:
            balance = self._get_user_balance(username)
        except:
            balance = {}

        result = {
            'balance': balance,
            'miners': miners,
            'transactions': transactions
        }

        return self._success(result)
    
    #                                                  #
    # =================== BALANCES =================== #
    #                                                  #

    def _row_to_balance(self, row):
        return {
            'username': str(row[0]),
            'balance': float(row[3])
        }

    def _get_balances(self):  
        statement = self._create_sql('SELECT * FROM Users')

        rows = self._sql_fetch_all(DATABASE, statement[0], statement[1])
        return [self._row_to_balance(row) for row in rows]

    def _fetch_balances(self):
        now = time()
        if now - self.last_balances_update < SAVE_TIME:
            return self.balances.copy()

        print(f'fetching balances from {DATABASE}')
        self.balances = self._get_balances()
        self.last_balances_update = time()

        return self.balances.copy()

    def api_get_balances(self):
        if 'username' in request.args:
            return self.api_get_user_balance(request.args['username'])

        if self.use_cache:
            balances = self._fetch_balances()
            return self._success(balances)

        try:
            balances = self._get_balances()
            return self._success(balances)
        except Exception as e:
            return self._error(f'Error fetching balances: {e}')


    # Get the balance of a user
    def _get_user_balance(self, username: str):
        row = self._sql_fetch_one(DATABASE, 'SELECT * FROM Users WHERE username = ? ORDER BY balance DESC', (username,))
        
        if not row:
            raise Exception(f'User \'{username}\' not found')

        return self._row_to_balance(row)

    def api_get_user_balance(self, username: str):
        if self.use_cache:
            balances = self._fetch_balances()
            balance = [b for b in balances if b['username'] == username][0] if 0 < len(balances) else {}
            return self._success(balance)

        try:
            balance = self._get_user_balance(username)
            return self._success(balance)
        except Exception as e:
            return self._error(f'Error fetching balance: {e}')

    #                                                      #
    # =================== TRANSACTIONS =================== #
    #                                                      #

    def _row_to_transaction(self, row):
        return {
            'datetime': str(row[0]),
            'sender': str(row[1]),
            'recipient': str(row[2]),
            'amount': float(row[3]),
            'hash': str(row[4]),
            'memo': str(row[5])
        }

    # Get all transactions
    def _get_transactions(self, username: Optional[str] = None, sender: Optional[str] = None, recipient: Optional[str] = None, sort: Optional[str] = None):
        # args = request.args.to_dict()
        args = {}

        # Remove all keys except for or, limit, sort
        if username:
            args['or'] = f'username,recipient:{str(username)}'

        ## The DB uses `username` for `sender`
        if sender:
            args['username'] = sender

        if recipient:
            args['recipient'] = recipient

        ## Adjust the sort key for datefield
        if sort:
            if 'datetime' in sort:
                args['sort'] = sort.replace('datetime', 'timestamp')

        statement = self._create_sql('SELECT * FROM Transactions', args)

        rows = self._sql_fetch_all(CONFIG_TRANSACTIONS, statement[0], statement[1])
        return [self._row_to_transaction(row) for row in rows]

    def _fetch_transactions(self):
        now = time()
        if now - self.last_transactions_update < 15:
            return self.transactions.copy()

        print(f'fetching transactions from {CONFIG_TRANSACTIONS}')
        self.transactions = self._get_transactions()
        self.last_transactions_update = time()

        return self.transactions.copy()
    
    def api_get_transactions(self):
        
        username = request.args.get('username', None)
        sender = request.args.get('sender', None)
        recipient = request.args.get('recipient', None)
        sort = request.args.get('sort', None)

        if self.use_cache:
            transactions = self._fetch_transactions()

            if username:
                transactions = [t for t in transactions if (t['sender'] == username or t['recipient'] == username)]

            elif sender and recipient:
                transactions = [t for t in transactions if (t['sender'] == sender and t['recipient'] == recipient)]
            
            elif sender:
                transactions = [t for t in transactions if t['sender'] == sender]

            elif recipient:
                transactions = [t for t in transactions if t['recipient'] == recipient]

            if sort:
                if 'datetime' in sort:
                    reverse = 'desc' not in sort
                    transactions = sorted(transactions, key=lambda k: k['datetime'], reverse=reverse) 
            
            return self._success(transactions)

        try:
            transactions = self._get_transactions(username=username, sender=sender, recipient=recipient, sort=sort)
            return self._success(transactions)
        except Exception as e:
            return self._error(f'Error fetching transactions: {e}')

    # Get all transactions
    def _get_user_transactions(self, username = None):
        username = request.args.get('username', username)
        sender = request.args.get('sender', None)
        recipient = request.args.get('recipient', None)
        sort = request.args.get('sort', None)

        if self.use_cache:
            transactions = self._fetch_transactions()

            if username:
                transactions = [t for t in transactions if (t['sender'] == username or t['recipient'] == username)]

            elif sender and recipient:
                transactions = [t for t in transactions if (t['sender'] == sender and t['recipient'] == recipient)]
            
            elif sender:
                transactions = [t for t in transactions if t['sender'] == sender]

            elif recipient:
                transactions = [t for t in transactions if t['recipient'] == recipient]

            if sort:
                if 'datetime' in sort:
                    transactions = sorted(transactions, key=lambda k: k['timestamp']) 
            
            return transactions

        return self._get_transactions(username=username, sort='timestamp:desc')

    # Get a transaction by its hash
    def _get_transaction(self, hash_id: str):
        if self.use_cache:
            self._fetch_transactions()
            transactions = self.transactions.copy()
            transaction = [t for t in transactions if t['hash'] == hash_id][0] if 0 < len(transactions) else {}
            return transaction

        row = self._sql_fetch_one(CONFIG_TRANSACTIONS, 'SELECT * FROM Transactions WHERE hash = ?', (hash_id,))
        
        if not row:
            raise Exception(f'Transaction \'{hash_id}\' does not exist')

        return self._row_to_transaction(row)

    def api_get_transaction(self, hash_id):
        try:
            transaction = self._get_transaction(hash_id)
            return self._success(transaction)
        except Exception as e:
            return self._error(f'Error fetching transaction: {e}')

    #                                                #
    # =================== MINERS =================== #
    #                                                #

    def _row_to_miner(self, row):
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
    def _fetch_miners(self):
        now = time()
        if now - self.last_miner_update < 20:
            return

        print(f'fetching miners from {CONFIG_MINERAPI}')
        miners = []
        try:
            rows = self._sql_fetch_all(CONFIG_MINERAPI, 'SELECT * FROM Miners')
            for row in rows:
                miners.append(self._row_to_miner(row))
        except Exception as e:
            print(f'Exception getting miners: {e}')
            pass
        
        self.minersapi = miners
        self.last_miner_update = time()

    # Get all miners
    def _get_miners(self):
        self._fetch_miners()
        miners = self.minersapi.copy()
        if 'username' in request.args.keys():
            miners = [m for m in miners if m['username'] == request.args['username']]
        return miners

    def api_get_miners(self):
        return self._success(self._get_miners())

    # Get specific miner by its `threadid`
    def _get_miner(self, threadid):
        miners = self._get_miners()

        miner = [m for m in miners if m['threadid'] == threadid]
        if miner:
            miner = miner[0]
        else:
            miner = {}
        
        return miner

    def api_get_miner(self, threadid):
        return self._success(self._get_miner(threadid))

    # Get miners for user
    def _get_user_miners(self, username):
        miners = self._get_miners()

        return [m for m in miners if m['username'] == username]

    #                                             #
    # =================== API =================== #
    #                                             #

    # Internal function to get API data from JSON file
    def _get_api_data(self):
        data = {}
        with open(API_JSON_URI, 'r') as f:
            try:
                data = json.load(f)
            except:
                pass

        return data

    def formatted_hashrate(self, hashrate: int, accuracy: int):
        """ Input: hashrate as int
            Output rounded hashrate with scientific prefix as string """
        if hashrate >= 900000000:
            prefix = " GH/s"
            hashrate = hashrate / 1000000000
        elif hashrate >= 900000:
            prefix = " MH/s"
            hashrate = hashrate / 1000000
        elif hashrate >= 900:
            prefix = " kH/s"
            hashrate = hashrate / 1000
        else:
            prefix = " H/s"
        return str(round(hashrate, accuracy)) + str(prefix)
    
    # Return API Data object
    def get_api_data(self):
        return jsonify(self._get_api_data())

cache = Cache(config=cache_conf)
app = DUCOApp()
cache.init_app(app)
