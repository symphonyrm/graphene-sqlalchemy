class Registry(object):
    def __init__(self, super_class):
        self.super_class = super_class
        self._registry = {}

    def register(self, cls):
        assert issubclass(cls, self.super_class), (
            "Only classes of type {} can be registered, "
            'received "{}"'
        ).format(self.super_class, cls.__name__)
        assert self.get_type_for_model(cls._meta.model) in [None, cls], (
            'SQLAlchemy model "{}" already associated with '
            'another type "{}".'
        ).format(cls._meta.model, self._registry[cls._meta.model])

        self._registry[cls._meta.model] = cls

    def get_type_for_model(self, model):
        return self._registry.get(model)


def get_registry(namespace, super_class):
    namespace.setdefault(super_class, Registry(super_class))
    return namespace[super_class]
