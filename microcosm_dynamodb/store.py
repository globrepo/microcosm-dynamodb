"""
Abstraction layer for persistence operations.

"""
from microcosm_dynamodb.errors import (
    ModelNotFoundError,
)
from microcosm_dynamodb.identifiers import new_object_id


class Store(object):

    def __init__(self, graph, model_class):
        self.graph = graph
        self.model_class = model_class
        # Give the model class a backref to allow model-oriented CRUD
        # short cuts while still having an abstraction layer we can replace.
        self.model_class.store = self

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
        instance = self.retrieve(identifier)
        self.engine.merge(new_instance)
        return instance

    def replace(self, identifier, new_instance):
        """
        Create or update a model.

        """
        try:
            return self.update(identifier, new_instance)
        except ModelNotFoundError:
            return self.create(new_instance)

    def delete(self, identifier):
        """
        Delete a model by primary key.

        :raises `ModelNotFoundError` if the row cannot be deleted.

        """
        return self._delete(self.model_class.id == identifier)

    def count(self, *criterion):
        """
        Count the number of models matching some criterion.

        """
        return self._query(*criterion).count()

    def search(self, *criterion, **kwargs):
        """
        Return the list of models matching some criterion.

        :param offset: pagination offset, if any
        :param limit: pagination limit, if any
        """
        query = self._query(*criterion)
        offset, limit = kwargs.get("offset"), kwargs.get("limit")
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

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
        return self.session.query(
            self.model_class
        ).filter(
            *criterion
        )
