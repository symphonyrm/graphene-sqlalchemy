import inflection

from sqlalchemy import Column, inspect
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import RelationshipProperty

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
    is_primary_key = bool(column.primary_key) and column.autoincrement and not column.foreign_keys

    return is_auto or is_primary_key


@dispatch()
def convert_name(cls: SQLAlchemyEditInputObjectType, model: DeclarativeMeta):
    return '{}EditInput'.format(model.__name__)


@dispatch()
def convert_name(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> str:
    if column.foreign_keys:
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
    return True
