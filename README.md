## Remo.ai demo ##

### Installation ###
This demo uses python and docker. 

For python `poetry` is used for dependency management. Please first install poetry by following the instructions here https://python-poetry.org/docs/#installation
TL;DR Install pipx and run `pipx install poetry`

Install this repo's poetry dependencies

    poetry install

Ensure docker is installed and running and that you have the docker-compose binary. If this is not available please check https://docs.docker.com/compose/install/ for instructions

Once this is working you can initialise docker which will setup MongoDB and Redis for use in this project

    docker-compose up -d

And confirm everything is running with

    docker ps

This should show mongo and redis up and running.

Config defaults set in config.py can be overridden by creating a custom `.env` file such as

```
MONGO_USER=someuser
MONGO_PASSWORD=somepassword
MONGO_DATABASE=somedbname
MONGO_CONNECTION_STRING=mongodb://localhost
```

### Running the application ###

The application can be started by running

    poetry shell
    python main.py

From within the project directory. 

## Running Tests ##

The project contains a test suite. This can be ran by running

    python -m pytest

From within a poetry shell `poetry shell` starts the shell as above

The tests are all unit tests and so don't require docker to run.


### Adding data to the running version ###

You can use CURL to add some basic data

`
curl -X POST http://localhost:8000/transactions \
     -H "Content-Type: application/json" \
     -d '{
           "user_id": "user1234",
           "amount": 10000,
           "currency": "USD",
           "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
           "type": "TRANSFER"
         }'
`

(Adding this transaction multiple times will eventually show RAPID_TRANSFER suspicion)

And then view the transactions for this user

`curl -X GET http://localhost:8000/transactions/suspicious/user1234`

For a more readable version it can be piped to jq i.e

`curl -X GET http://localhost:8000/transactions/suspicious/user1234 | jq`


### API Specification ###

There are two endpoints in this implementation. 

*POST /transactions*

*BODY*

    user_id - String
    amount - Number
    currency - String
    timestamp - ISODate (i.e. 2024-11-18T13:25:49 as String)
    type - One of DEPOSIT, WITHDRAWAL, TRANSFER, OTHER

*RESPONSE*

    HTTP 201 Created

    id - String - id of the transaction,
    user_id - String
    amount - Number
    currency - String
    timestamp - ISODate
    type - One of DEPOSIT, WITHDRAWAL, TRANSFER, OTHER
    is_suspicious - Boolean 
    suspicious_reasons - An array of values, each value is one of HIGH_VOLUME_TRANSACTION, FREQUENT_SMALL_TRANSACTIONS, FREQUENT_SMALL_TRANSACTIONS  
    
If the sent transaction does not meet the request as described above an HTTP 422 is returned with the error


GET /transactions/suspicious/{user_id}

* RESPONSE *

    HTTP 200 OK
    
    Response contains an array of transactions, each being
    id - String - id of the transaction,
    user_id - String
    amount - Number
    currency - String
    timestamp - ISODate
    type - One of DEPOSIT, WITHDRAWAL, TRANSFER, OTHER
    is_suspicious - Boolean 
    suspicious_reasons - An array of values, each value is one of HIGH_VOLUME_TRANSACTION, FREQUENT_SMALL_TRANSACTIONS, FREQUENT_SMALL_TRANSACTIONS  

    If there are no transactions an empty array is sent


## Assumptions Made ##

* In the specification it eas mentioned to "Flag a user" rather than "Flag a transaction" however I thought it best to flag the individual transaction due to it making more sense and having context. The user is technically flagged if they have recent suspicious activity that can be found from calling the suspicious transactions endpoint for that user.
* When calculating transactions with limits I included the current transaction. If an alert should be flagged on the 5th transaction for example, I count the current transaction and look for 4 in the database.





