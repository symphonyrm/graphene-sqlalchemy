from collections import Iterable

from graphene.types.base import BaseType
from sqlalchemy import Column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import CompositeProperty, RelationshipProperty

from .field_types import OrmLike
from .namespace import dispatch


def explicitly_ignored(
    name: str,
    only_fields: Iterable,
    exclude_fields: Iterable
) -> bool:
    is_not_in_only = bool(only_fields) and name not in only_fields
    is_excluded = name in exclude_fields

    return is_not_in_only or is_excluded


@dispatch()
def ignore_field(
    orm_prop: OrmLike,
    cls: type,
    only_fields: Iterable,
    exclude_fields: Iterable,
) -> bool:
    func = ignore_field.dispatch(type(orm_prop), cls, type(only_fields), type(exclude_fields))
    return func(orm_prop, cls, only_fields, exclude_fields)


@dispatch()
def ignore_field(
    column: Column,
    cls: BaseType,
    only_fields: Iterable,
    exclude_fields: Iterable,
) -> bool:
    return explicitly_ignored(column.name, only_fields, exclude_fields)


# TODO: Check if composite has a `name` field or similar. Would be surprising if not
@dispatch()
def ignore_field(
    composite: CompositeProperty,
    cls: BaseType,
    only_fields: Iterable,
    exclude_fields: Iterable,
) -> bool:
    return explicitly_ignored(composite.name, only_fields, exclude_fields)


@dispatch()
def ignore_field(
    hybrid: hybrid_property,
    cls: BaseType,
    only_fields: Iterable,
    exclude_fields: Iterable,
) -> bool:
    return explicitly_ignored(hybrid.__name__, only_fields, exclude_fields)


@dispatch()
def ignore_field(
    relationship: RelationshipProperty,
    cls: BaseType,
    only_fields: Iterable,
    exclude_fields: Iterable,
) -> bool:
    return explicitly_ignored(relationship.key, only_fields, exclude_fields)
