"""
Support for building models.

Every model must inherit from `Model` and should inherit from the `EntityMixin`.

"""
from uuid import UUID

from flywheel import Field, Model as BaseModel


class Model(BaseModel):

    # XXX We do not strictly need to have a default id field, however flywheel enforces
    # us to have one via the metaclass. We need this baseclass to perform the UUID to string
    # conversion below and so we add this default which can be over-ridden by derived classes.
    id = Field(hash_key=True)

    def __init__(self, **kwargs):
        # XXX flywheel does not currently play nice with uuid.UUID types.
        # microcosm-flask automatically converts ids from URLs to UUID,
        # and so this is required for now as a bridge.
        if 'id' in kwargs and isinstance(kwargs['id'], UUID):
            kwargs['id'] = str(kwargs['id'])
        super(Model, self).__init__(**kwargs)


class IdentityMixin(object):
    """
    Define model identity in terms of members.

    This form of equality isn't always appropriate, but it's a good place to start,
    especially for writing test assertions.

    """
    def __eq__(self, other):
        return type(other) is type(self) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__dict__)


class SmartMixin(object):
    """
    Define a model with short cuts for CRUD operations against its `Store`.

    These short cuts still delegate responsibility for persistence to the store (which must be
    instantiated first).

    """
    def create(self):
        return self.__class__.store.create(self)

    def delete(self):
        return self.__class__.store.delete(self.id)

    def update(self):
        return self.__class__.store.update(self.id, self)

    def replace(self):
        return self.__class__.store.replace(self.id, self)

    @classmethod
    def search(cls, *criterion, **kwargs):
        return cls.store.search(*criterion, **kwargs)

    @classmethod
    def count(cls, *criterion):
        return cls.store.count(*criterion)

    @classmethod
    def retrieve(cls, identifier):
        return cls.store.retrieve(identifier)


class EntityMixin(IdentityMixin, SmartMixin):
    """
    Convention for persistent entities combining other mixins.

    """
    pass
