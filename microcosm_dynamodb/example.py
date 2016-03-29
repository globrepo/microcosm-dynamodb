"""
Example models and store usage.

"""
from flywheel import Field, Model

from microcosm.api import binding
from microcosm_dynamodb.store import Store


class Company(Model):
    """
    A company has a name.

    """
    name = Field()


class CompanyStore(Store):
    pass


@binding("company_store")
def configure_company_store(graph):
    return CompanyStore(graph, Company)
