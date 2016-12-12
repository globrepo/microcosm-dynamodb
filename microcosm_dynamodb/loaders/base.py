"""
Microcosm compatible configuration loader using DynamoDB.

"""
from abc import ABCMeta, abstractmethod, abstractproperty
from getpass import getuser
from six import string_types
from warnings import warn

from botocore.exceptions import ClientError
from boto3 import Session
from boto3.dynamodb.conditions import Attr
from credstash import paddedInt

from microcosm.loaders import expand_config


def table_name(prefix, service):
    """
    Generate the table name for a given service.

    """
    return "{}-{}-config".format(prefix, service)


class DynamoDBLoader(object):
    """
    Load config data from a DynamoDB table, assuming one table per service.

    Configuration keys will be split into nested dictionaries based on the current separator.

    """
    __metaclass__ = ABCMeta

    def __init__(self,
                 prefix=None,
                 separator="__",
                 profile_name=None,
                 region=None):
        """
        :param prefix: table name prefix

        """
        # default to user-specific name for safety
        self.prefix = prefix or getuser().lower()
        self.separator = separator
        self.profile_name = profile_name
        self.region = region

    def __call__(self, metadata, version=None):
        """
        Build configuration from metadata.

        """
        service = metadata if isinstance(metadata, string_types) else metadata.name
        return expand_config(
            dict(self.items(service, version=version)),
            separator=self.separator,
        )

    @abstractproperty
    def value_type(self):
        """
        Return the value type to use.

        The value type is polymorphic and should be a namedtuple with no keys overlapping the
        the dynamodb table's index and sort keys.

        """
        pass

    @abstractmethod
    def decode(self, value_type):
        """
        Get a plaintext value from the value type.

        """
        pass

    @abstractmethod
    def encode(self, value):
        """
        Convert a plaintext value to the value type.

        """
        pass

    def all(self, service, version=None):
        """
        Query all service config rows.

        """
        # request all fields; since `key` is reserved, we have to use a substitution
        field_names = [
            "#k" if field == "key" else field
            for field in self.value_type._fields
        ]

        attribute_names = {
            "#n": "name",
        }

        if "#k" in field_names:
            attribute_names["#k"] = "key"

        # filter by version, if any
        if version is not None:
            filter_expression = Attr("version").eq(version)
        else:
            filter_expression = None

        try:
            return self._table(service).scan(
                Select="SPECIFIC_ATTRIBUTES",
                ProjectionExpression=", ".join(["#n"] + field_names),
                FilterExpression=filter_expression,
                ConsistentRead=True,
                ExpressionAttributeNames=attribute_names,
            )
        except ClientError as error:
            # we probably don't have logging configured yet, so use `warnings`
            warn(
                "Unable to query configuration from {}: {}".format(
                    table_name(self.prefix, service),
                    error.message,
                ),
            )
            raise

    def items(self, service, version=None):
        """
        Generate configuration key rows as items.

        """
        return [
            (row["name"], self.decode(self.value_type(**{
                name: value
                for name, value in row.items()
                if name not in ("name", "version")
            })))
            for row in self.all(service, version)["Items"]
        ]

    def put(self, service, name, value, version=None):
        """
        Put a configuration value.

        """
        item = dict(
            name=name,
            version=version or paddedInt(1),
        )
        item.update(self.encode(value)._asdict())
        self._table(service).put_item(
            Item=item,
        )

    def get(self, service, name, version=None):
        """
        Get a configuration value.

        """
        result = self._table(service).get_item(
            Key=dict(
                name=name,
                version=version or paddedInt(1),
            )
        )

        item = result.get("Item")
        if item is None:
            return None

        return self.decode(self.value_type(**{
            key: value
            for key, value in item.items()
            if key not in ("name", "version")
        }))

    def delete(self, service, name, version=None):
        """
        Delete a configuration value.

        """
        result = self._table(service).delete_item(
            Key=dict(
                name=name,
                version=version or paddedInt(1),
            ),
        )
        return result

    def _table(self, service):
        session = Session(profile_name=self.profile_name)
        dynamodb = session.resource('dynamodb', region_name=self.region)
        return dynamodb.Table(table_name(self.prefix, service))
