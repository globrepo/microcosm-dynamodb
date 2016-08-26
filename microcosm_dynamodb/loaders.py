"""
Microcosm compatible configuration loader.

"""
from base64 import b64decode, b64encode
from collections import namedtuple

from boto3 import client, Session
from boto3.dynamodb.conditions import Key
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Hash.HMAC import HMAC
from Crypto.Util import Counter


TableDefinition = namedtuple("TableDefinition", ["name", "read_capacity", "write_capacity"])
PlaintextValue = namedtuple("PlaintextValue", ["plaintext"])
EncryptedValue = namedtuple("EncryptedValue", ["cyphertext_key", "cyphertext", "cyphertext_hmac"])


DEFAULT_TABLE_DEFINITION = TableDefinition(
    name="config",
    read_capacity=1,
    write_capacity=1,
)


CONFIG_NAME = "config_name"
SERVICE_NAME = "service_service"


class DynamoDBLoader(object):
    """
    Load config data from a DynamoDB table.

    Usage:
        loader.put("test", "foo", PlaintextValue("bar"))
        print loader.get("test", "foo").plaintext

    Only configuration for the current service name (via `metadata.name`) are loaded.

    Configuration keys will be split into nested dictionaries based on the current separator.

    """
    def __init__(self, table_definition=DEFAULT_TABLE_DEFINITION, separator=".", profile_name=None, region=None):
        self.table_definition = table_definition
        self.separator = separator
        self.profile_name = profile_name
        self.region = region

    @property
    def value_type(self):
        """
        Return the value type to use.

        The value type is polymorphic and should be a namedtuple with no keys overlapping the
        the dynamodb table's index and sort keys.

        """
        return PlaintextValue

    def get_plaintext(self, value):
        """
        Get a plaintext value from the value type.

        """
        return value.plaintext

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
                    "AttributeName": SERVICE_NAME,
                    "AttributeType": "S",
                },
                {
                    "AttributeName": CONFIG_NAME,
                    "AttributeType": "S",
                },
            ],
            KeySchema=[
                {
                    "AttributeName": SERVICE_NAME,
                    "KeyType": "HASH",
                },
                {
                    "AttributeName": CONFIG_NAME,
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
            ProjectionExpression=", ".join([CONFIG_NAME] + list(self.value_type._fields)),
            ConsistentRead=True,
            KeyConditionExpression=Key(SERVICE_NAME).eq(service),
        )

    def items(self, service):
        """
        Generate configuration key rows as items.

        """
        return [
            (row[CONFIG_NAME], self.get_plaintext(self.value_type(**{
                name: value
                for name, value in row.items()
                if name != CONFIG_NAME
            })))
            for row in self.all(service)["Items"]
        ]

    def put(self, service, name, value):
        """
        Put a configuration value.

        """
        if not isinstance(value, self.value_type):
            raise Exception("Expected value to be an instance of: {}".format(
                self.value_type.__name__,
            ))
        item = {
            SERVICE_NAME: service,
            CONFIG_NAME: name,
        }
        item.update(vars(value))
        self.table.put_item(
            Item=item,
        )

    def get(self, service, name):
        """
        Get a configuration value.

        """
        result = self.table.get_item(
            Key={
                SERVICE_NAME: service,
                CONFIG_NAME: name,
            },
        )

        item = result.get("Item")
        if item is None:
            return None

        return self.value_type(**{
            key: value
            for key, value in item.items()
            if key not in (SERVICE_NAME, CONFIG_NAME)
        })

    def delete(self, service, name):
        """
        Delete a configuration value.

        """
        result = self.table.delete_item(
            Key={
                SERVICE_NAME: service,
                CONFIG_NAME: name,
            },
        )
        return result

    def __call__(self, metadata):
        """
        Build configuration.

        """
        config = {}
        for name, value in self.items(metadata.name):
            # expand name into nested dictionaries
            name_parts = name.split(self.separator)
            config_part = config
            for name_part in name_parts[:-1]:
                config_part = config.setdefault(name_part, {})
            # save value
            config_part[name_parts[-1]] = value
        return config


class EncryptedDynamoDBLoader(DynamoDBLoader):
    """
    Encrypt configuration using KMS.

    Usage:
        loader.put("test", "foo", loader.encrypt("bar"))
        print loader.decrypt(loader.get("test", "foo"))

    Code adapted with much appreciation to credstash. See:

    https://github.com/fugue/credstash/blob/master/credstash.py

    """
    def __init__(self, kms_key, **kwargs):
        super(EncryptedDynamoDBLoader, self).__init__(**kwargs)
        self.kms_key = kms_key

    @property
    def value_type(self):
        return EncryptedValue

    def get_plaintext(self, value):
        return self.decrypt(value)

    def encrypt(self, plaintext, context=None):
        if not context:
            context = {}

        session = Session(profile_name=self.profile_name)
        kms = session.client('kms', region_name=self.region)
        kms_response = kms.generate_data_key(
            KeyId=self.kms_key,
            EncryptionContext=context,
            NumberOfBytes=64,
        )
        data_key = kms_response['Plaintext'][:32]
        hmac_key = kms_response['Plaintext'][32:]
        wrapped_key = kms_response['CiphertextBlob']
        enc_ctr = Counter.new(128)
        encryptor = AES.new(data_key, AES.MODE_CTR, counter=enc_ctr)
        c_text = encryptor.encrypt(plaintext)
        # compute an HMAC using the hmac key and the ciphertext
        hmac = HMAC(hmac_key, msg=c_text, digestmod=SHA256)
        b64hmac = hmac.hexdigest()

        return EncryptedValue(
            b64encode(wrapped_key).decode('utf-8'),
            b64encode(c_text).decode('utf-8'),
            b64hmac,
        )

    def decrypt(self, value, context=None):
        if not context:
            context = {}

        session = Session(profile_name=self.profile_name)
        kms = session.client('kms', region_name=self.region)

        # Check the HMAC before we decrypt to verify ciphertext integrity
        kms_response = kms.decrypt(
            CiphertextBlob=b64decode(value.cyphertext_key),
            EncryptionContext=context,
        )
        key = kms_response['Plaintext'][:32]
        hmac_key = kms_response['Plaintext'][32:]
        hmac = HMAC(
            hmac_key,
            msg=b64decode(value.cyphertext),
            digestmod=SHA256,
        )
        if hmac.hexdigest() != value.cyphertext_hmac:
            raise Exception("Computed HMAC does not match stored HMAC")
        dec_ctr = Counter.new(128)
        decryptor = AES.new(key, AES.MODE_CTR, counter=dec_ctr)
        plaintext = decryptor.decrypt(b64decode(value.cyphertext)).decode("utf-8")
        return plaintext
