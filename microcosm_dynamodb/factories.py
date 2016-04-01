"""
Factory that configures flywheel DynamoDB ORM-like framework.

"""
from flywheel import Engine

from microcosm.api import defaults


@defaults(
    region="us-west-2",
)
def configure_flywheel_engine(graph):
    """
    Create the flywheel engine.

    """
    namespace = ()
    if graph.metadata.testing:
        namespace = 'test'

    engine = Engine(namespace=namespace)
    engine.connect_to_region(graph.config.dynamodb.region)

    return engine
