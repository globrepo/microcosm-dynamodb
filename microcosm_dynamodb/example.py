"""
Example models and store usage.

"""
from flywheel import Field

from microcosm.api import binding
from microcosm_dynamodb.models import EntityMixin, Model
from microcosm_dynamodb.store import Store


class Company(EntityMixin, Model):
    """
    A company has a name.

    """
    id = Field(hash_key=True)
    name = Field()


class CompanyStore(Store):
    pass


class Employee(EntityMixin, Model):
    """
    A employee has a name and associated company.

    """
    company_id = Field(hash_key=True)
    id = Field(range_key=True)
    name = Field()


class EmployeeStore(Store):
    pass


@binding("company_store")
def configure_company_store(graph):
    return CompanyStore(graph, Company)


@binding("employee_store")
def configure_employee_store(graph):
    return EmployeeStore(graph, Company)
