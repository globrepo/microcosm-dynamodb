"""
Identifier utilities.

"""
from uuid import uuid4, UUID


def new_object_id():
    """
    Use randomized UUIDs by default.

    """
    return str(uuid4())


def normalize_id(identifier):
    """
    Flywheel does not currently play nice with uuid.UUID types.

    Related libraries (e.g. microcosm-flask) use UUIDs; convert to string,

    """
    if isinstance(identifier, UUID):
        return str(identifier)
    return identifier
