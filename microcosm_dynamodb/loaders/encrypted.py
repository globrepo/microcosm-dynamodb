"""
Encrypted DynamoDB config loader using credstash.

Code adapted with much appreciation to credstash. As much as possible, uses credstash code,
but currently prevented from full reuse because of difficulty configurating credstash's KMS key.

See: https://github.com/fugue/credstash/blob/master/credstash.py

"""
from collections import namedtuple

from boto3 import Session
from credstash import KeyService, open_aes_ctr_legacy, seal_aes_ctr_legacy

from microcosm_dynamodb.loaders.base import DynamoDBLoader


# match credstash key names
EncryptedValue = namedtuple("EncryptedValue", ["key", "contents", "hmac"])


class EncryptedDynamoDBLoader(DynamoDBLoader):
    """
    A credstash-compatible microcosm config loader using KMS-encrypted DynamoDB data.

    Usage:

        from microcosm.metadata import Metadata
        from microcosm_dynamodb.loaders.encrypted import EncryptedDynamoDBLoader

        metadata = Metadata("myservice")
        loader = EncryptedDynamoDBLoader(kms_key="alias/mykey")
        loader.put(metadata.name, "key", "value")
        print loader.get(metadata.name, "key")
        print loader(metadata)
        loader.delete(metadata.name, "key")

    """
    def __init__(self, kms_key, **kwargs):
        super(EncryptedDynamoDBLoader, self).__init__(**kwargs)
        self.kms_key = kms_key

    @property
    def value_type(self):
        return EncryptedValue

    def decode(self, value_type):
        return self.decrypt(value_type)

    def encode(self, value):
        return self.encrypt(value)

    def decrypt(self, value, context=None):
        if not context:
            context = {}
        session = Session(profile_name=self.profile_name)
        kms = session.client('kms', region_name=self.region)
        key_service = KeyService(kms, None, context)
        return open_aes_ctr_legacy(
            key_service,
            dict(
                key=value.key,
                contents=value.contents,
                hmac=value.hmac,
            )
        )

    def encrypt(self, plaintext, context=None):
        if not context:
            context = {}
        session = Session(profile_name=self.profile_name)
        kms = session.client('kms', region_name=self.region)
        key_service = KeyService(kms, None, context)
        sealed = seal_aes_ctr_legacy(
            key_service,
            plaintext,
        )
        return EncryptedValue(
            sealed["key"],
            sealed["contents"],
            sealed["hmac"],
        )
