"""
Encrypted DynamoDB config loader using credstash.

Code adapted with much appreciation to credstash. As much as possible, uses credstash code,
but currently prevented from full reuse because of difficulty configurating credstash's KMS key.

See: https://github.com/fugue/credstash/blob/master/credstash.py

"""
from base64 import b64decode, b64encode
from collections import namedtuple

from boto3 import Session
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Hash.HMAC import HMAC
from Crypto.Util import Counter

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

        # Check the HMAC before we decrypt to verify ciphertext integrity
        kms_response = kms.decrypt(
            CiphertextBlob=b64decode(value.key),
            EncryptionContext=context,
        )
        key = kms_response['Plaintext'][:32]
        hmac_key = kms_response['Plaintext'][32:]
        hmac = HMAC(
            hmac_key,
            msg=b64decode(value.contents),
            digestmod=SHA256,
        )
        if hmac.hexdigest() != value.hmac:
            raise Exception("Computed HMAC does not match stored HMAC")
        dec_ctr = Counter.new(128)
        decryptor = AES.new(key, AES.MODE_CTR, counter=dec_ctr)
        plaintext = decryptor.decrypt(b64decode(value.contents)).decode("utf-8")
        return plaintext

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
