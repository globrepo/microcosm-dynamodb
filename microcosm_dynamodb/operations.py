"""
Common database operations.

"""


def create_all(graph):
    """
    Create all database tables.

    """
    graph.dynamodb.create_schema(test=graph.config.testing)


def drop_all(graph):
    """
    Drop all database tables.

    """
    graph.dynamodb.delete_schema(test=graph.config.testing)


def recreate_all(graph):
    """
    Drop and add back all database tables.

    """
    drop_all(graph)
    create_all(graph)
