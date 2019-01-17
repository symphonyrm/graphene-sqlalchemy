# -*- coding: utf-8 -*-

import inflection

from sqlalchemy import Column, inspect
from sqlalchemy.orm import RelationshipProperty

from .input_type import SQLAlchemyInputObjectType
from ..api import dispatch, explicitly_ignored, get_registry


class SQLAlchemyCreateInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


@dispatch()
def set_registry_class(cls: SQLAlchemyCreateInputObjectType):
    return SQLAlchemyCreateInputObjectType


@dispatch()
def ignore_field(
    column: Column,
    cls: SQLAlchemyCreateInputObjectType,
    only_fields: list,
    exclude_fields: list,
) -> bool:
    name = column.name
    explicit = explicitly_ignored(name, only_fields, exclude_fields)

    auto_fields = ['created_at', 'updated_at']
    is_auto = bool(column.server_default) and inflection.underscore(name) in auto_fields
    is_primary_key = bool(column.primary_key) and column.autoincrement and not column.foreign_keys

    return explicit or is_auto or is_primary_key


# TODO: This is the only reason we might need `model` on `convert_name`.
#       Is there a way to avoid that?
@dispatch()
def convert_name(
    column: Column,
    cls: SQLAlchemyCreateInputObjectType,
    model: object
) -> str:
    if column.foreign_keys:
        end = '_id'
        name = column.name
        relationships = [
            rel
            for rel in inspect(model).relationships
            if column in rel.local_columns
        ]
        if relationships:
            name = relationships[0].key
        elif name.endswith(end):
            name = column.name[:-len(end)]
        return 'attach_to_{name}'.format(name=name)
    return column.name


@dispatch()
def convert_name(
    relationship: RelationshipProperty,
    cls: SQLAlchemyCreateInputObjectType,
    model: object
) -> str:
    return 'create_and_attach_to_{name}'.format(name=relationship.key)


@dispatch()
def is_nullable(column: Column, cls: SQLAlchemyCreateInputObjectType) -> bool:
    if column.foreign_keys:
        return True
    return bool(getattr(column, "nullable", True))
