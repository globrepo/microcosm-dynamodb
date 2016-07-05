"""
Abstraction layer for persistence operations.

"""
from uuid import UUID
import logging

from microcosm_dynamodb.errors import (
    ModelNotFoundError,
)
from microcosm_dynamodb.identifiers import new_object_id


TEST_TABLE_PREFIX = "test_"


class Store(object):

    def __init__(self, graph, model_class):
        self.graph = graph
        self.model_class = model_class
        # Give the model class a backref to allow model-oriented CRUD
        # short cuts while still having an abstraction layer we can replace.
        self.model_class.store = self
        # Each model must be registered with the engine exactly once.
        self._register()

    @property
    def engine(self):
        return self.graph.dynamodb

    def new_object_id(self):
        """
        Injectable id generation to facilitate mocking.

        """
        return new_object_id()

    def create(self, instance):
        """
        Create a new model instance.

        """
        if instance.id is None:
            instance.id = self.new_object_id()

        # XXX flywheel does not currently play nice with uuid.UUID types.
        # microcosm-flask automatically converts ids from URLs to UUID,
        # and so this is required for now as a bridge.
        if isinstance(instance.id, UUID):
            instance.id = str(instance.id)

        self.engine.save(instance)
        return instance

    def retrieve(self, identifier, *criterion):
        """
        Retrieve a model by primary key and zero or more other criteria.

        :raises `NotFound` if there is no existing model

        """
        return self._retrieve(
            self.model_class.id == identifier,
            *criterion
        )

    def update(self, identifier, new_instance):
        """
        Update an existing model with a new one.

        :raises `ModelNotFoundError` if there is no existing model

        """
        # XXX flywheel does not currently play nice with uuid.UUID types.
        # microcosm-flask automatically converts ids from URLs to UUID,
        # and so this is required for now as a bridge.
        if isinstance(identifier, UUID):
            identifier = str(identifier)

        instance = self.engine.get(self.model_class, id=identifier)
        if not instance:
            raise ModelNotFoundError()

        new_instance = self._merge(instance, from_=new_instance)
        self.engine.sync(new_instance)

        return new_instance

    def _merge(self, to, from_):
        """
        Merge a flywheel.Model instance into another one.
        This uses flywheel's __dirty__ set which tracks any fields
        which have unsaved modifications.

        """
        assert type(to) == type(from_)

        for field_name in from_.__dirty__:
            setattr(to, field_name, getattr(from_, field_name))
        return to

    def replace(self, identifier, new_instance):
        """
        Create or update a model.

        """
        try:
            return self.update(identifier, new_instance)
        except ModelNotFoundError:
            return self.create(new_instance)

    def delete(self, identifier, *criterion):
        """
        Delete a model by primary key and optional additional criteria.

        :raises `ModelNotFoundError` if the row cannot be deleted.

        """
        return self._delete(
            self.model_class.id == identifier,
            *criterion
        )

    def count(self, *criterion, **kwargs):
        """
        Count the number of models matching some criterion.

        """
        if not (criterion or kwargs):
            logging.warning(
                "count() - DynamoDB Table scans are extremely slow, avoid counting without filters when possible."
            )
            return sum(1 for item in self.engine.scan(self.model_class).gen())
        else:
            query = self._query(*criterion)
            query = self._filter(query, **kwargs)
            return query.count()

    def search(self, *criterion, **kwargs):
        """
        Return the list of models matching some criterion.

        :param limit: pagination limit, if any
        """
        if criterion:
            query = self._query(*criterion)
        else:
            query = self.engine.scan(self.model_class)

        query = self._filter(query, **kwargs)
        query = self._order_by(query, **kwargs)
        return query.all()

    def _order_by(self, query, **kwargs):
        """
        Add an order by clause to a (search) query. For DynamoDB, using flywheel,
        we can support ordering using a an index, e.g updating query with:

        >>> query = query.index('timestamp-index')

        By default, is a noop.

        """
        return query

    def _filter(self, query, **kwargs):
        """
        Filter a query with user-supplied arguments.

        :param limit: pagination limit, if any

        """
        limit = kwargs.get("limit")
        if limit is not None:
            query = query.limit(limit)
        return query

    def _retrieve(self, *criterion):
        """
        Retrieve a model by some criteria.

        :raises `ModelNotFoundError` if the row cannot be deleted.

        """
        try:
            return self._query(*criterion).one()
        except Exception as error:
            raise ModelNotFoundError(error)

    def _delete(self, *criterion):
        """
        Delete a model by some criterion.

        Avoids race-condition check-then-delete logic by checking the count of affected rows.

        :raises `ResourceNotFound` if the row cannot be deleted.

        """
        count = self._query(*criterion).delete()
        if count == 0:
            raise ModelNotFoundError
        return True

    def _query(self, *criterion):
        """
        Construct a query for the model.

        """
        return self.engine.query(
            self.model_class
        ).filter(
            *criterion
        )

    def _register(self):
        self.graph.dynamodb.register(self.model_class)
