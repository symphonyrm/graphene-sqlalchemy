import inflection

from graphene import Dynamic, Field, List
from sqlalchemy import Column, inspect
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import interfaces, RelationshipProperty

from .create_input_type import SQLAlchemyCreateInputObjectType
from .input_type import SQLAlchemyInputObjectType
from ..api import dispatch, get_registry


class SQLAlchemyEditInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


@dispatch()
def set_registry_class(cls: SQLAlchemyEditInputObjectType):
    return SQLAlchemyEditInputObjectType


@dispatch()
def ignore_field(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    auto_fields = ['created_at', 'updated_at']
    is_auto = bool(column.server_default) and inflection.underscore(column.name) in auto_fields

    return is_auto


@dispatch()
def convert_name(cls: SQLAlchemyEditInputObjectType, model: DeclarativeMeta):
    return '{}EditInput'.format(model.__name__)


@dispatch()
def convert_name(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> str:
    if column.foreign_keys and not column.primary_key:
        name = column.name.rsplit('_id', 1)[0]
        relationships = [
            rel
            for rel in inspect(model).relationships
            if column in rel.local_columns
        ]
        if relationships:
            name = relationships[0].key
        return 'attach_to_{name}'.format(name=name)
    return column.name


@dispatch()
def convert_name(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    relationship: RelationshipProperty,
) -> str:
    return 'create_and_attach_to_{name}'.format(name=relationship.key)


@dispatch()
def is_nullable(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    is_primary_key = bool(column.primary_key) and column.autoincrement

    return not is_primary_key


@dispatch()
def construct_fields(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    relationship: RelationshipProperty,
):
    name = convert_name(cls, model, relationship)
    direction = relationship.direction
    model = relationship.mapper.entity

    def dynamic_type():
        # TODO: Think about changing the registry interface
        #       This feels clunky
        registry = get_registry(SQLAlchemyCreateInputObjectType)
        _type = registry.get_type_for_model(model)
        if not _type:
            return None
        if direction == interfaces.MANYTOONE or not relationship.uselist:
            return Field(_type)
        elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
            if _type._meta.connection:
                return createConnectionField(_type._meta.connection)
            return Field(List(_type))

    setattr(cls, name, Dynamic(dynamic_type))
