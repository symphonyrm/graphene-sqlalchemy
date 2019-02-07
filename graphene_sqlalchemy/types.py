from typing import Callable

from sqlalchemy.orm.exc import NoResultFound

from graphene import Field, ID
from graphene.relay import Connection
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs

from .api import construct_fields, dispatch, get_connection, get_interfaces, get_registry, set_registry_class
from .utils import get_query, check_connection, check_mapped_class, check_mapped_instance


class SQLAlchemyObjectTypeOptions(ObjectTypeOptions):
    model = None  # type: Model
    connection = None  # type: Type[Connection]
    id = None  # type: str
    arguments = None
    resolver = None  # type: Callable


class SQLAlchemyObjectType(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls,
        model=None,
        skip_registry=False,
        interfaces=(),
        id=None,
        _meta=None,
        **options
    ):
        check_mapped_class(model)

        _meta = _meta or SQLAlchemyObjectTypeOptions(cls)
        _meta.connection = get_connection(cls, model)
        _meta.fields = _meta.fields or {}
        _meta.id = id or "id"
        _meta.model = model
        interfaces = interfaces or get_interfaces(cls, model)

        # _meta.fields.update(
        yank_fields_from_attrs(
            construct_fields(cls, model),
            _as=Field)#)

        super(SQLAlchemyObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta, interfaces=interfaces, **options
        )

        if not skip_registry:
            registry = get_registry(set_registry_class(cls))
            registry.register(cls)

    @classmethod
    def is_type_of(cls, root, info):
        if isinstance(root, cls):
            return True
        check_mapped_instance(root)

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
        args = cls._meta.arguments or {
            'id': ID(required=True)
        }
        resolver = cls._meta.resolver or cls.get_instance

        return Field(cls, args=args, resolver=resolver)
