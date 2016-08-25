"""
Factory that configures flywheel DynamoDB ORM-like framework.

"""
from os import environ

from flywheel import Engine

from microcosm.api import defaults


@defaults(
    namespace="",
    region=environ.get("AWS_DEFAULT_REGION"),
)
def configure_flywheel_engine(graph):
    """
    Create the flywheel engine.

    """
    namespace = graph.config.dynamodb.namespace

    if graph.metadata.testing:
        from microcosm_dynamodb.mockengine import MockEngine
        engine = MockEngine(namespace="test-")
    else:
        engine = Engine(namespace=namespace)

    engine.connect_to_region(graph.config.dynamodb.region)
    return engine
