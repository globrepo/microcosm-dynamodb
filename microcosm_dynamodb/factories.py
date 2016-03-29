"""
Factory that configures flywheel DynamoDB ORM-like framework.

"""
from flywheel import Engine

from microcosm.api import binding, defaults


@binding("dynamodb")
@defaults(
    region="us-west-2",
)
def configure_flywheel_engine(graph):
    """
    Create the flywheel engine.

    """
    engine = Engine()
    engine.connect_to_region(graph.config.dynamodb.region)
    return engine
