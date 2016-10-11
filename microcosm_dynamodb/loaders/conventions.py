"""
Load configuration according to conventions:

 1. Use a KMS key based on the environment name.

    The key is expected to be an alias named <environment>-conf.

 2. Load versioned configuration based on the `MICROCOSM_CONFIG_VERSION` and
    `MICROCOSM_ENVIRONMENT` environment variables.

    If present, only the given config version is used; otherwise, dynamodb db loading is skipped.

 3. Encode semantic versions using the credstash version string


"""
from os import environ

from credstash import paddedInt
from microcosm.loaders import load_from_dict

from microcosm_dynamodb.loaders.encrypted import EncryptedDynamoDBLoader


def load_from_dynamodb(environment=None):
    """
    Fluent shorthand for the whole brevity thing.

    """
    if environment is None:
        try:
            environment = environ["MICROCOSM_ENVIRONMENT"]
        except KeyError:
            # noop
            return load_from_dict(dict())

    return VersionedEncryptedDynamoDBLoader(environment)


def kms_key_name(environment):
    return "alias/{}-config".format(environment)


def compute_version_string(version, base=1000):
    """
    Compute the version string to use for a specific version.

    Normalizes the version using credstash's integer padding.

    Drops the patch version under the assumption that we wish to simply restart
    existing services rather than update their initialization configuration to use
    a new version definition. However, retains padding space for the patch version
    for forwards-compatibility.

    """
    major, minor, patch = version.split(".", 2)
    return paddedInt(base ** 3 * int(major) + base ** 2 * int(minor))


class VersionedEncryptedDynamoDBLoader(EncryptedDynamoDBLoader):

    def __init__(self, environment):
        """
        Construct using KMS key based on environment name.

        """
        super(VersionedEncryptedDynamoDBLoader, self).__init__(
            kms_key=kms_key_name(environment),
            prefix=environment,
        )

    def __call__(self, metadata):
        """
        Conditionally load configuration based on the MICROCOSM_SERVICE_VERSION environment variable.

        """
        version = environ.get("MICROCOSM_CONFIG_VERSION")

        if version is None:
            # skip dynamodb loading; useful when AWS is not accessible
            return {}

        return super(VersionedEncryptedDynamoDBLoader, self).__call__(
            metadata,
            version=compute_version_string(version),
        )
