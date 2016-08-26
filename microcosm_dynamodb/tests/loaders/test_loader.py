"""
Test basic loading logic (without any DynamoDB) integration.

"""
from collections import namedtuple

from microcosm.metadata import Metadata
from hamcrest import (
    assert_that,
    equal_to,
    is_,
)
from mock import patch

from microcosm_dynamodb.loaders.base import DynamoDBLoader


DummyValue = namedtuple("TestValue", "dummy")


SIMPLE_ITEM = dict(
    name="foo",
    dummy="bar",
    version="0000000000000000001",
)


NESTED_ITEM = dict(
    name="bar.baz",
    dummy="foo",
    version="0000000000000000001",
)


MOCK_ITEMS = [
    SIMPLE_ITEM,
    NESTED_ITEM,
]


class DummyDynamoDBLoader(DynamoDBLoader):

    @property
    def value_type(self):
        return DummyValue

    def decode(self, value):
        return value.dummy

    def encode(self, value):
        return self.value_type(value)


class TestDynamoDBLoader(object):

    def setup(self):
        self.loader = DummyDynamoDBLoader()
        self.metadata = Metadata("dummy")

    def test_load_empty_configuration(self):
        with patch.object(self.loader, "_table") as mocked:
            mocked.return_value.scan.return_value = dict(
                Items=[],
            )

            assert_that(self.loader(self.metadata), is_(equal_to(dict())))

        mocked.assert_called_with(self.metadata.name)
        mocked.return_value.scan.assert_called()

    def test_load_non_empty_configuration(self):
        with patch.object(self.loader, "_table") as mocked:
            mocked.return_value.scan.return_value = dict(
                Items=MOCK_ITEMS,
            )

            assert_that(self.loader(self.metadata), is_(equal_to(dict(
                foo="bar",
                bar=dict(
                    baz="foo",
                ),
            ))))

        mocked.assert_called_with(self.metadata.name)
        mocked.return_value.scan.assert_called()

    def test_put(self):
        with patch.object(self.loader, "_table") as mocked:
            self.loader.put(self.metadata.name, "foo", "bar")

        mocked.assert_called_with(self.metadata.name)
        mocked.return_value.put_item.assert_called_with(
            Item=dict(
                dummy="bar",
                name="foo",
                version="0000000000000000001",
            ),
        )

    def test_get(self):
        with patch.object(self.loader, "_table") as mocked:
            mocked.return_value.get_item.return_value = dict(
                Item=SIMPLE_ITEM,
            )
            assert_that(self.loader.get(self.metadata.name, "foo"), is_(equal_to("bar")))

        mocked.assert_called_with(self.metadata.name)
        mocked.return_value.get_item.assert_called_with(
            Key=dict(
                name="foo",
                version="0000000000000000001",
            ),
        )

    def test_delete(self):
        with patch.object(self.loader, "_table") as mocked:
            self.loader.delete(self.metadata.name, "foo")

        mocked.assert_called_with(self.metadata.name)
        mocked.return_value.delete_item.assert_called_with(
            Key=dict(
                name="foo",
                version="0000000000000000001",
            ),
        )
