"""
Persistence tests using examples.

"""
from hamcrest import (
    assert_that,
    calling,
    contains_inanyorder,
    equal_to,
    is_,
    raises,
)
from nose.plugins.attrib import attr

from microcosm.api import create_object_graph
from microcosm_dynamodb.errors import (
    ModelNotFoundError,
)
from microcosm_dynamodb.example import Company
from microcosm_dynamodb.operations import recreate_all


@attr('aws')
class TestCompany(object):

    def setup(self):
        self.graph = create_object_graph(name="example", testing=True, import_name="microcosm_dynamodb")
        self.company_store = self.graph.company_store

        recreate_all(self.graph)

    def test_create_retrieve_company(self):
        """
        Should be able to retrieve a company after creating it.

        """
        company = Company(name="name").create()

        retrieved_company = Company.retrieve(company.id)
        assert_that(retrieved_company.name, is_(equal_to("name")))

    def test_create_delete_company(self):
        """
        Should not be able to retrieve a company after deleting it.

        """
        company = Company(name="name").create()
        company.delete()

        assert_that(calling(Company.retrieve).with_args(company.id), raises(ModelNotFoundError))

    def test_create_search_count_company(self):
        """
        Should be able to search and count companies after creation.

        """
        company1 = Company(name="name1").create()
        company2 = Company(name="name2").create()

        assert_that(Company.count(), is_(equal_to(2)))
        assert_that([company.id for company in Company.search()], contains_inanyorder(company1.id, company2.id))

    def test_create_search_limit_company(self):
        """
        Should be able to search companies with a limit after creation.

        """
        Company(name="name1").create()
        Company(name="name2").create()

        assert_that(len(list(company for company in Company.search(limit=1))), is_(equal_to(1)))

    def test_create_update_company(self):
        """
        Should be able to update a company after creating it.

        """
        company = Company(name="name").create()

        company.name = "new_name"
        updated_company = company.update()
        assert_that(updated_company.name, is_(equal_to("new_name")))

        retrieved_company = Company.retrieve(company.id)
        assert_that(retrieved_company.name, is_(equal_to("new_name")))
