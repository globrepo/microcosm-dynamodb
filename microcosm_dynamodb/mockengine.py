"""
Simple in-memory Engine mock.

"""
from microcosm_dynamodb.errors import ModelNotFoundError


class MockQuery(object):
    def __init__(self, engine, model_class):
        self._engine = engine
        self._model_class = model_class
        self._criterion = None
        self._limit = None

    @property
    def instances(self):
        return self._engine.models[self._model_class]

    @instances.setter
    def instances(self, value):
        self._engine.models[self._model_class] = value

    def filter(self, *criterion):
        self._criterion = criterion
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    def check_criterion(self, instance):
        # XXX criterion checking is not implemented
        return True

    def all(self):
        return list(self.gen())

    def delete(self):
        keep = []
        count = 0
        for instance in self.instances:
            if self.check_criterion(instance):
                count += 1
            else:
                keep += instance
        self.instances = keep
        return count

    def gen(self):
        count = 0
        for id, instance in self.instances.items():
            if not self.check_criterion(instance):
                continue
            yield instance
            count += 1
            if count == self._limit:
                break

    def one(self):
        for instance in self.gen():
            return instance
        raise ModelNotFoundError


class MockEngine(object):
    def __init__(self, namespace):
        self.namespace = namespace
        self.region = None
        self.models = {}

    def connect_to_region(self, region):
        self.region = region

    def register(self, model):
        self.models.setdefault(model, {})

    def delete_schema(self):
        pass

    def create_schema(self):
        pass

    def save(self, instance):
        self.models[instance.__class__][instance.id] = instance

    def scan(self, model_class):
        return self.query(model_class)

    def sync(self, instance):
        if instance.id in self.models[instance.__class__]:
            self.save(instance)
        else:
            raise ModelNotFoundError

    def query(self, model_class):
        return MockQuery(self, model_class)

    def get(self, model_class, **identifiers):
        # XXX identifier lookup is not fully featured
        return self.models[model_class][identifiers["id"]]
