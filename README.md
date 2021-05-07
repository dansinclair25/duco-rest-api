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



`GET /transactions/from/<username>/` - returns a list of all transactions sent from `<username>. If no transactions exist, returns an empty list.`

Example:

 `GET /transactions/from/revox`

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



`GET /transactions/to/<username>` - returns a list of all transactions sent to `<username>`. If no transactions exist, returns an empty list.

Example:

 `GET /transactions/to/revox`

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



`GET /transactions/from/<sender>/to/<recipient>` - returns a list of all transactions sent from `<sender>` to `<recipient>`. If no transactions exist, returns an empty list.

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

