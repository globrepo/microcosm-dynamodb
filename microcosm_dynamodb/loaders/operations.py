"""
Create a configuration DynamoDB table.

"""
from argparse import ArgumentParser

from credstash import createDdbTable

from microcosm_dynamodb.loaders.base import table_name


def create_config_table():
    """
    Create a DynamoDB table for storing configuration.

    Under normal circumstances this table should be created out-of-band with an automated tool
    (such as Terraform or CloudFormation) and along with appropriate access controls.

    """
    parser = ArgumentParser()
    parser.add_argument("--prefix")
    parser.add_argument("--region")
    parser.add_argument("--service", required=True)
    args = parser.parse_args()

    table = table_name(prefix=args.prefix, service=args.service)

    createDdbTable(table=table, region=args.region)
