# duco-rest-api

This is a simple REST API using Flask that links in directly to the DUCO databases to return transactions, and balances.

----

## Usage

1. Install requirements using `pip3 install -r requirements.txt`
2. Run it using `gunicorn wsgi:app` 
3. Locally, this is available on `127.0.0.1:5000`

----

## Endpoints

### Users

- **URL**

  `/users/<username>`

- **Method**

  `GET`

- **Success Response**

  **Code:** `200`

  **Content:**

  ```json
  {
    "result": {
      "balance": {
        "balance": 1047.796283515931,
        "username": "dansinclair25"
      },
      "miners": [
        {
          "accepted": 1038,
          "algorithm": "DUCO-S1",
          "diff": 2000,
          "hashrate": 11086,
          "identifier": "ESP32 4",
          "rejected": 0,
          "sharetime": 5.677812,
          "software": "ESP32 CORE2 Miner v2.52",
          "threadid": "140479274537872",
          "username": "dansinclair25"
        },
        {
          "accepted": 1269,
          "algorithm": "DUCO-S1",
          "diff": 5,
          "hashrate": 195,
          "identifier": "unos",
          "rejected": 0,
          "sharetime": 10.116792,
          "software": "Official AVR Miner (DUCO-S1A) v2.49",
          "threadid": "140479268060240",
          "username": "dansinclair25"
        }
      ],
      "transactions": [
        {
          "amount": 9.855,
          "datetime": "29/04/2021 14:43:37",
          "hash": "a04b2a4dced85cc093dcdc9e57af197e34e295a3",
          "memo": "Bot coins to DUCO exchange",
          "recipient": "dansinclair25",
          "sender": "coinexchange"
        },
        {
          "amount": 22.845,
          "datetime": "27/04/2021 14:30:14",
          "hash": "f60a135e0d1c2f0ad1f03eb55c87e4de9bd9f888",
          "memo": "Bot coins to DUCO exchange",
          "recipient": "dansinclair25",
          "sender": "coinexchange"
        },
        {
          "amount": 0.01,
          "datetime": "26/04/2021 09:22:03",
          "hash": "183eccfe465fc23600cf07e1ec55beaf57ff2486",
          "memo": "faucet",
          "recipient": "dansinclair25",
          "sender": "ducofaucet"
        }
      ]
    },
    "success": true
  }
  ```

  

### Transactions

* **URL**

  `/transactions`

* **Method**

  `GET`

* **URL Params**

  **Optional Filters:**

  `username=[alphanumeric]` - to get all transactions (sent or received) by a user. Only to be used with no other filters
  `amount=[float]` - to get all transactions with a specific amount
  `recipient=[alphanumeric]` - to get all transactions received by a user
  `sender=[alphanumeric]` - to get all transactions sent by a user

  **Optional Others:**
  `sort=[key](:desc)` - sort the returned transactions by a given key. Direction is ascending by default. Only 1 sort per request.
  `limit=[integer]` - only return a certain number of results. Only 1 limit per request.

* **Success Response**

  **Code:** `200`

  **Content:**

```json
{
  "success": true,
  "result": [
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
}
```

* **Error Response**

  **Code:** `400`
  **Content:**

```json
{
  "success": false,
  "message": "Error fetching transactions"
}
```



### Transaction

* **URL**
  `/transactions/<hash>`

* **Method**
  `GET`

* **Success Reponse**
  **Code:** `200`
  **Content:**

  ```json
  {
    "success": True,
    "result": {
        "amount": 5,
        "datetime": "18/04/2021 09:27:16",
        "hash": "b11019a12589831ccab2447bb69b08de51206693",
        "memo": "-",
        "recipient": "ATAR4XY",
        "sender": "revox"
      }
  }
  ```

* **Error Response**

  **Code:** `400`
  **Content:**

  ```json
  {
    "success": false,
    "message": "Error fetching transaction"
  }
  ```

  

### Balances

* **URL**

  `/balances`

* **Method**

  `GET`

* **Success Response**

  **Code:** `200`

  **Content:**

```json
{
  "success": true,
  "result": [
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
}
```

* **Error Response**

  **Code:** `400`
  **Content:**

```json
{
  "success": false,
  "message": "Error fetching balances"
}
```



### Balance

* **URL**

  `/balances/<username>`

* **Method**

  `GET`

* **Success Response**

  **Code:** `200`

  **Content:**

```json
{
  "success": true,
  "result": {
    "balance": 45756.09652071045,
    "username": "coinexchange"
  }
}
```

* **Error Response**

  **Code:** `400`
  **Content:**

```json
{
  "success": false,
  "message": "Error fetching balance"
}
```



### Miners

* **URL**

  `/miners`

* **Method**

  `GET`

* **URL Params**

  **Optional Filters:**

  `username=[alphanumeric]` - to get all miners belonging to a user.

* **Success Response**

  **Code:** `200`

  **Content:**

```json
{
  "success": true,
  "result": [
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
}
```

* **Error Response**

  **Code:** `400`
  **Content:**

```json
{
  "success": false,
  "message": "Error fetching miners"
}
```



### Miner

* **URL**

  `/miners/<threadid>`

* **Method**

  `GET`

* **Success Response**

  **Code:** `200`

  **Content:**

```json
{
  "success": true,
  "result": {
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
  }
}
```

* **Error Response**

  **Code:** `400`
  **Content:**

```json
{
  "success": false,
  "message": "Error fetching miner"
}
```



### Statistics

* **URL**

  `/statistics`

* **Method**

  `GET`

* **Success Response**

  **Code:** `200`

  **Content:**

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



## Examples

Fetch all transactions for `revox`:
`/transactions?username=revox`

Fetch all transactions in date order (oldest first):
`/transactions?sort=datetime:desc`

Fetch all transactions from `dansinclair25` to `treadstone42`:
`/transactions?sender=dansinclair25&recipient=treadstone42`

Fetch the last 10 transactions:
`/transactions?sort=datetime&limit=10`

Fetch all balances sorted by amount (highest amount first):
`/balances?sort=balance:desc`

Fetch balance for `revox`:
`/balances/revox`

Fetch all miners for `dansinclair25`:
`/miners?username=dansinclair25`



## Known Issues

- No sorting or filtering (other than `username`) on miners.
- Returned status code for errors maybe incorrect value (although still an error status code).
