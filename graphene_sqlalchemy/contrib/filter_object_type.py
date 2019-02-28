from functools import partial

from graphene import Dynamic, relay
from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy_utils.generic import GenericRelationshipProperty

from .countable_connection import CountableConnection
from .dbid_interface import DatabaseId
from .filter_connection import InstrumentedQuery
from ..api import dispatch, dynamic_type
from ..types import SQLAlchemyObjectType


class SQLAlchemyFilterObjectType(SQLAlchemyObjectType):
    class Meta:
        abstract = True


    def resolve_db_id(self, info, **args):
        # pylint: disable=no-member
        keys = self.__mapper__.primary_key_from_instance(self)
        return tuple(keys) if len(keys) > 1 else keys[0]


@dispatch()
def set_registry_class(cls: SQLAlchemyFilterObjectType):
    return SQLAlchemyFilterObjectType


@dispatch()
def get_connection(cls: SQLAlchemyFilterObjectType, model: DeclarativeMeta):
    name = "{}Connection".format(cls.__name__)
    return CountableConnection.create_type(name, node=cls)


@dispatch()
def get_connection_field(cls: SQLAlchemyFilterObjectType, model: DeclarativeMeta):
    return InstrumentedQuery(cls)


@dispatch()
def get_interfaces(cls: SQLAlchemyFilterObjectType, model: DeclarativeMeta):
    return [
        relay.Node,
        DatabaseId,
    ]


@dispatch()
def convert_name(cls: SQLAlchemyFilterObjectType, model: DeclarativeMeta):
    return model.__name__


@dispatch()
def convert_name( # pylint: disable=function-redefined
    cls: SQLAlchemyFilterObjectType,
    model: DeclarativeMeta,
    column: Column,
) -> str:
    name = column.name
    is_primary_key = bool(column.primary_key) and column.autoincrement and not column.foreign_keys

    if is_primary_key and name == 'id':
        return 'db_id'
    return name


@dispatch()
def construct_fields(
    cls: SQLAlchemyFilterObjectType,
    model: DeclarativeMeta,
    relationship: GenericRelationshipProperty,
):
    foreign_models = relationship.get_all_related_models()
    generic = partial(dynamic_type, cls, model, relationship, foreign_models)
    setattr(cls, relationship.key, Dynamic(generic))
