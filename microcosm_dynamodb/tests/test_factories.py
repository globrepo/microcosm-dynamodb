"""
Factory tests.

"""
from flywheel import Engine
from hamcrest import (
    assert_that,
    instance_of,
    is_,
)

from microcosm.api import create_object_graph


def test_configure_flywheel_engine():
    """
    Should create the `flywheel` engine

    """
    graph = create_object_graph(name="example", testing=True, import_name="microcosm_dynamodb")
    assert_that(graph.dynamodb, is_(instance_of(Engine)))
