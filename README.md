# microcosm-dynamodb

Opinionated persistence with AWS DynamoDB.


[![Circle CI](https://circleci.com/gh/globality-corp/microcosm-dynamodb/tree/develop.svg?style=svg)](https://circleci.com/gh/globality-corp/microcosm-dynamodb/tree/develop)


## Usage

This project includes example models and persistence stores. Assuming the testing
database exists (see below), the following demonstrates basic usage:

    from microcosm.api import create_object_graph
    from microcosm_dynamodb.context import SessionContext
    from microcosm_dynamodb.example import Company

    # create the object graph
    graph = create_object_graph(name="example", testing=True)

    # wire up the persistence layer to the (testing) database
    [company_store] = graph.use("company_store")

    # set up a session
    with SessionContext(graph) as context:

        # drop and create database tables; *only* do this for testing
        context.recreate_all()

        # create a model
        company = company_store.create(Company(name="Acme"))

        # prints 1
        print company_store.count()


## Convention

Models:

 -  Persistent models use a `flywheel` declarative base class
 -  Persistent operations pass through a unifying `Store` layer
 -  Persistent operations favor explicit queries and deletes over automatic relations and cascades


## Configuration

To change the database region:

    config.dynamodb.region = "us-west-2"


## Test Setup

TODO: Write
