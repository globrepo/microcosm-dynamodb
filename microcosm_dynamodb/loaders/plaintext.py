"""
Microcosm compatible configuration loader using plaintext (unencrypted) values.

"""
from collections import namedtuple

from microcosm_dynamodb.loaders.base import DynamoDBLoader


PlaintextValue = namedtuple("PlaintextValue", ["plaintext"])


class PlaintextDynamoDBLoader(DynamoDBLoader):
    """
    A microcosm config loader using plaintext (unencrypted) DynamoDB data.

    Usage:

        from microcosm.metadata import Metadata
        from microcosm_dynamodb.loaders.plaintext import PlaintextDynamoDBLoader

        metadata = Metadata("myservice")
        loader = PlaintextDynamoDBLoader()
        loader.put(metadata.name, "key", "value")
        print loader.get(metadata.name, "key")
        print loader(metadata)
        loader.delete(metadata.name, "key")

    """

    @property
    def value_type(self):
        return PlaintextValue

    def decode(self, value):
        return value.plaintext

    def encode(self, value):
        return self.value_type(value)
