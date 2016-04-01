# microcosm-dynamodb

Opinionated persistence with AWS DynamoDB.


[![Circle CI](https://circleci.com/gh/globality-corp/microcosm-dynamodb/tree/develop.svg?style=svg)](https://circleci.com/gh/globality-corp/microcosm-dynamodb/tree/develop)


## Usage

This project includes example models and persistence stores. Assuming the testing
database exists (see below), the following demonstrates basic usage:

    from microcosm.api import create_object_graph
    from microcosm_dynamodb.example import Company

    # create the object graph
    graph = create_object_graph(name="example", testing=True)

    # wire up the persistence layer to the (testing) database
    [company_store] = graph.use("company_store")

    # create a model
    company = company_store.create(Company(name="Acme"))

    # prints 1
    print company_store.count()


## Convention

Models:

 -  Persistent models use a `flywheel` declarative base class
 -  Persistent operations pass through a unifying `Store` layer


## Configuration

To change the database region:

    config.dynamodb.region = "us-west-2"


## Test Setup

Tests (and automated builds) act as the "example" microservice and will by default use a dedicated namespace, prefixing all created Table names with 'test'.

To run all tests that do not involve actually hitting AWS APIs, you can exclude tests using the 'aws' tag:

    nosetests -a '!aws'
