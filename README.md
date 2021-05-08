# duco-rest-api

This is a simple REST API using Flask that links in directly to the DUCO databases to return transactions, and balances.

## Usage

1. Install requirements using `pip3 install -r requirements.txt`
2. Run it using `flask run` 

## Endpoints

### Transactions
`GET /transactions` - returns a list of all transactions. If no transactions exist, returns an empty list.

Example:

`GET /transactions`

```json
[
  {
    "amount": 5,
    "datetime": "18/04/2021 09:19:32",
    "hash": "d2b690c337fa7b74b97c52ae8d1fa3bbab31034b",
    "memo": "abc",
    "recipient": "Bilaboz",
    "sender": "revox"
  },
  {
    "amount": 1.5,
    "datetime": "18/04/2021 09:20:21",
    "hash": "2c3829febd60906580065c95ebff809d3977dc2b",
    "memo": "-",
    "recipient": "revox",
    "sender": "coinexchange"
  },
  {
    "amount": 5,
    "datetime": "18/04/2021 09:27:16",
    "hash": "b11019a12589831ccab2447bb69b08de51206693",
    "memo": "-",
    "recipient": "ATAR4XY",
    "sender": "revox"
  }
]
```



`GET /transactions/<username>` - returns a list of all transactions both sent and received by `<username>` . If no transactions exist, returns an empty list.

Example:

 `GET /transactions/revox`

```json
[
  {
    "amount": 5,
    "datetime": "18/04/2021 09:19:32",
    "hash": "d2b690c337fa7b74b97c52ae8d1fa3bbab31034b",
    "memo": "abc",
    "recipient": "Bilaboz",
    "sender": "revox"
  },
  {
    "amount": 1.5,
    "datetime": "18/04/2021 09:20:21",
    "hash": "2c3829febd60906580065c95ebff809d3977dc2b",
    "memo": "-",
    "recipient": "revox",
    "sender": "coinexchange"
  },
  {
    "amount": 5,
    "datetime": "18/04/2021 09:27:16",
    "hash": "b11019a12589831ccab2447bb69b08de51206693",
    "memo": "-",
    "recipient": "ATAR4XY",
    "sender": "revox"
  }
]
```



`GET /transactions/sender/<username>/` - returns a list of all transactions sent from `<username>`. If no transactions exist, returns an empty list.

Example:

 `GET /transactions/sender/revox`

```json
[
  {
    "amount": 5,
    "datetime": "18/04/2021 09:19:32",
    "hash": "d2b690c337fa7b74b97c52ae8d1fa3bbab31034b",
    "memo": "abc",
    "recipient": "Bilaboz",
    "sender": "revox"
  },
  {
    "amount": 5,
    "datetime": "18/04/2021 09:27:16",
    "hash": "b11019a12589831ccab2447bb69b08de51206693",
    "memo": "-",
    "recipient": "ATAR4XY",
    "sender": "revox"
  }
]
```



`GET /transactions/recipient/<username>` - returns a list of all transactions sent to `<username>`. If no transactions exist, returns an empty list.

Example:

 `GET /transactions/recipient/revox`

```json
[
  {
    "amount": 1.5,
    "datetime": "18/04/2021 09:20:21",
    "hash": "2c3829febd60906580065c95ebff809d3977dc2b",
    "memo": "-",
    "recipient": "revox",
    "sender": "coinexchange"
  }
]
```



`GET /transactions/sender/<sender>/recipient/<recipient>` - returns a list of all transactions sent from `<sender>` to `<recipient>`. If no transactions exist, returns an empty list.

Example:

 `GET /transactions/from/revox/to/Bilaboz`

```json
[
  {
    "amount": 5,
    "datetime": "18/04/2021 09:19:32",
    "hash": "d2b690c337fa7b74b97c52ae8d1fa3bbab31034b",
    "memo": "abc",
    "recipient": "Bilaboz",
    "sender": "revox"
  }
]
```



### Balances

`GET /balances` - returns a list of all balances. If no balances exist, returns an empty list.

Example:

`GET /balances`

```json
[
  {
    "balance": 47071.64148509737,
    "username": "chipsa"
  },
  {
    "balance": 45756.09652071045,
    "username": "coinexchange"
  },
  {
    "balance": 31812.522314445283,
    "username": "aarican"
  }
]
```



`GET /balances/<username>` - returns the balance of `<username>`. If no balance exists, returns an empty dictionary.

Exmaple:

`GET /balances/revox`

```json
{
  "balance": 2499.283867309529,
  "username": "revox"
}
```



### Miners

`GET /miners` - returns a list of all miners. If no miners exist, returns an empty list.

Example:

`GET /miners`

```json
[
  {
    "accepted": 2935,
    "algorithm": "DUCO-S1",
    "diff": 5,
    "hashrate": 168,
    "id": "139797360490200",
    "identifier": "ProMiniRig Node6",
    "is estimated": "False",
    "rejected": 0,
    "sharetime": 3.324042,
    "software": "Official AVR Miner (DUCO-S1A) v2.45",
    "user": "MPM"
  },
  {
    "accepted": 1234,
    "algorithm": "DUCO-S1",
    "diff": 98765,
    "hashrate": 169000,
    "id": "139797360421968",
    "identifier": "PC Miner 1",
    "is estimated": "False",
    "rejected": 0,
    "sharetime": 2.065604,
    "software": "Official PC Miner (DUCO-S1) v2.45",
    "user": "dansinclair25"
  }
]
```



`GET /miners/<username>` - returns a list of miners for `<username>`. If no miners exist, returns an empty list

Example:

`GET /miners/dansinclair25`

```json
[
    {
    "accepted": 1234,
    "algorithm": "DUCO-S1",
    "diff": 98765,
    "hashrate": 169000,
    "id": "139797360421968",
    "identifier": "PC Miner 1",
    "is estimated": "False",
    "rejected": 0,
    "sharetime": 2.065604,
    "software": "Official PC Miner (DUCO-S1) v2.45",
    "user": "dansinclair25"
  }
]
```



### API Data

`GET /api` - return a object containing all of the API Data available in the `api.json` file

Example:

`GET /api`

```json
{
  "Active connections": 6596,
  "Active workers": {
    "revox": 70,
    "bilaboz": 1
  },
  "All-time mined DUCO": 936804.132060897,
  "Current difficulty": 212500,
  "DUCO-S1 hashrate": "1.6 GH/s",
  "Duco JustSwap price": 0.00791081,
  "Duco Node-S price": 0.001013,
  "Duco price": 0.0112407,
  "Duino-Coin Server API": "github.com/revoxhere/duino-coin",
  "Last block hash": "f76f5524b9...",
  "Last update": "08/05/2021 11:43:51 (UTC)",
  "Mined blocks": 1593769271,
  "Miners": "server.duinocoin.com/miners.json",
  "Open threads": 14,
  "Pool hashrate": "1.68 GH/s",
  "Registered users": 4837,
  "Server CPU usage": 43.2,
  "Server RAM usage": 26.3,
  "Server version": 2.4,
  "Top 10 richest miners": [
    "47079.374 DUCO - chipsa",
    "45719.8415 DUCO - coinexchange",
    "31812.5223 DUCO - aarican",
    "28407.0982 DUCO - NodeSBroker",
    "25776.1024 DUCO - cjmick",
    "24408.7585 DUCO - roboalex2",
    "21206.7592 DUCO - sabartheman",
    "20611.379 DUCO - Homer22",
    "20080.3961 DUCO - mikesb",
    "16471.0628 DUCO - PHR9",
    "15486.71 DUCO - MaddestHoldings"
  ],
  "XXHASH hashrate": "118.5 MH/s"
}
```

