"""
Microcosm compatible configuration loader.

"""
from collections import namedtuple

from boto3 import client, Session
from boto3.dynamodb.conditions import Key


TableDefinition = namedtuple("TableDefinition", ["name", "read_capacity", "write_capacity"])


DEFAULT_TABLE_DEFINITION = TableDefinition(
    name="config",
    read_capacity=1,
    write_capacity=1,
)


ConfigKey = "ConfigKey"
ConfigValue = "ConfigValue"
ServiceName = "ServiceName"


class DynamoDBLoader(object):
    """
    Load config data from a DynamoDB table containing `ServiceName`, `ConfigKey`, `ConfigValue` tuples.

    Only configuration for the current service name (via `metadata.name`) are loaded.

    Configuration keys will be split into nested dictionaries based on the current separator.

    """
    def __init__(self, table_definition=DEFAULT_TABLE_DEFINITION, separator=".", profile_name=None, region=None):
        self.table_definition = table_definition
        self.separator = separator
        self.profile_name = profile_name
        self.region = region

    @property
    def table(self):
        session = Session(profile_name=self.profile_name)
        dynamodb = session.resource('dynamodb', region_name=self.region)
        return dynamodb.Table(self.table_definition.name)

    def create_table(self):
        """
        Create a table with a primary key (the service name) and a sort key (the config key name).

        Under normal circumstances this table should be created out-of-band with an automated tool
        (such as Terraform or CloudFormation) and along with appropriate access controls.

        """
        dynamodb_client = client("dynamodb")
        dynamodb_client.create_table(
            TableName=self.table_definition.name,
            AttributeDefinitions=[
                {
                    "AttributeName": ServiceName,
                    "AttributeType": "S",
                },
                {
                    "AttributeName": ConfigKey,
                    "AttributeType": "S",
                },
            ],
            KeySchema=[
                {
                    "AttributeName": ServiceName,
                    "KeyType": "HASH",
                },
                {
                    "AttributeName": ConfigKey,
                    "KeyType": "RANGE",
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": self.table_definition.read_capacity,
                "WriteCapacityUnits": self.table_definition.write_capacity,
            }
        )

    def all(self, service):
        """
        Query all service config rows.

        """
        return self.table.query(
            Select="SPECIFIC_ATTRIBUTES",
            ProjectionExpression=", ".join([ConfigKey, ConfigValue]),
            ConsistentRead=True,
            KeyConditionExpression=Key(ServiceName).eq(service),
        )

    def items(self, service):
        """
        Generate configuration key rows as items.

        """
        return [
            (row[ConfigKey], row[ConfigValue])
            for row in self.all(service)["Items"]
        ]

    def put(self, service, key, value):
        """
        Put a configuration value.

        """
        self.table.put_item(
            Item={
                ServiceName: service,
                ConfigKey: key,
                ConfigValue: value,
            },
        )

    def get(self, service, key):
        """
        Get a configuration value.

        """
        result = self.table.get_item(
            Key={
                ServiceName: service,
                ConfigKey: key,
            },
        )
        return result.get("Item")

    def delete(self, service, key):
        """
        Delete a configuration value.

        """
        result = self.table.delete_item(
            Key={
                ServiceName: service,
                ConfigKey: key,
            },
        )
        return result

    def __call__(self, metadata):
        """
        Build configuration.

        """
        config = {}
        for key, value in self.items(metadata.name):
            # expand key into nested dictionaries
            key_parts = key.split(self.separator)
            config_part = config
            for key_part in key_parts[:-1]:
                config_part = config.setdefault(key_part, {})
            # save value
            config_part[key_parts[-1]] = value
        return config
