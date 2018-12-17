from collections import OrderedDict
from typing import Callable

from sqlalchemy.inspection import inspect as sqlalchemyinspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.exc import NoResultFound

from graphene import Field, ID
from graphene.relay import Connection, Node
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs

from .api import construct_fields, get_registry
from .registry import Registry
from .utils import get_query, is_mapped_class, is_mapped_instance


class SQLAlchemyObjectTypeOptions(ObjectTypeOptions):
    model = None  # type: Model
    registry = None  # type: Registry
    connection = None  # type: Type[Connection]
    id = None  # type: str
    arguments = None
    resolver = None  # type: Callable


class SQLAlchemyObjectType(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls,
        model=None,
        registry=None,
        skip_registry=False,
        only_fields=(),
        exclude_fields=(),
        connection=None,
        connection_class=None,
        use_connection=None,
        interfaces=(),
        id=None,
        _meta=None,
        **options
    ):
        assert is_mapped_class(model), (
            "You need to pass a valid SQLAlchemy Model in " '{}.Meta, received "{}".'
        ).format(cls.__name__, model)

        if not registry:
            registry = get_registry(SQLAlchemyObjectType)

        assert isinstance(registry, Registry), (
            "The attribute registry in {} needs to be an instance of "
            'Registry, received "{}".'
        ).format(cls.__name__, registry)

        sqla_fields = yank_fields_from_attrs(
            construct_fields(
                model,
                registry,
                only_fields,
                exclude_fields,
                cls=cls
            ), _as=Field
        )

        if use_connection is None and interfaces:
            use_connection = any(
                (issubclass(interface, Node) for interface in interfaces)
            )

        if use_connection and not connection:
            # We create the connection automatically
            if not connection_class:
                connection_class = Connection

            connection = connection_class.create_type(
                "{}Connection".format(cls.__name__), node=cls
            )

        if connection is not None:
            assert issubclass(connection, Connection), (
                "The connection must be a Connection. Received {}"
            ).format(connection.__name__)

        if not _meta:
            _meta = SQLAlchemyObjectTypeOptions(cls)

        _meta.model = model
        _meta.registry = registry

        if _meta.fields:
            _meta.fields.update(sqla_fields)
        else:
            _meta.fields = sqla_fields

        _meta.connection = connection
        _meta.id = id or "id"

        super(SQLAlchemyObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta, interfaces=interfaces, **options
        )

        if not skip_registry:
            registry.register(cls)

    @classmethod
    def is_type_of(cls, root, info):
        if isinstance(root, cls):
            return True
        if not is_mapped_instance(root):
            raise Exception(('Received incompatible instance "{}".').format(root))
        return isinstance(root, cls._meta.model)

    @classmethod
    def get_query(cls, info):
        model = cls._meta.model
        return get_query(model, info.context)

    @classmethod
    def get_node(cls, info, id):
        try:
            return cls.get_query(info).get(id)
        except NoResultFound:
            return None

    def resolve_id(self, info):
        keys = self.__mapper__.primary_key_from_instance(self)
        return tuple(keys) if len(keys) > 1 else keys[0]

    @classmethod
    def get_instance(cls, model, info, id):
        try:
            return cls.get_query(info).get(id)
        except NoResultFound:
            return None

    @classmethod
    def Field(cls, *args, **kwargs):
        args = cls._meta.arguments
        resolver = cls._meta.resolver
        if not args:
            args = {
                'id': ID(required=True)
            }
        if not resolver:
            resolver = cls.get_instance

        return Field(cls, args=args, resolver=resolver)
