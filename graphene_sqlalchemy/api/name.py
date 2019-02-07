from inspect import getmro

from graphene.types.base import BaseType
from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import CompositeProperty, RelationshipProperty
# from sqlalchemy_utils.generic import GenericRelationshipProperty
from ..generic import GenericRelationshipProperty

from .field_types import OrmLike
from .namespace import dispatch


@dispatch()
def convert_name(
    cls: type,
    model: DeclarativeMeta,
    orm_prop: OrmLike
) -> str:
    func = None
    model_mro = getmro(model)
    if model_mro:
        model_type = model_mro[0]
        func = convert_name.dispatch(cls, model_type, type(orm_prop))
    if not func:
        func = convert_name.dispatch(cls, type(model), type(orm_prop))
    # func = convert_name.dispatch(cls, type(model), type(orm_prop))
    return func(cls, model, orm_prop)


@dispatch()
def convert_name(
    cls: type,
    model: DeclarativeMeta,
) -> str:
    func = convert_name.dispatch(cls, type(model))
    return func(cls, model)


@dispatch()
def convert_name(
    cls: BaseType,
    model: DeclarativeMeta,
    orm_prop: OrmLike,
) -> str:
    return get_name(orm_prop)


@dispatch()
def get_name(column: Column) -> str:
    return column.name


# TODO: Check if composite has a `name` field or similar. Would be surprising if not
@dispatch()
def get_name(composite: CompositeProperty) -> str:
    return composite.name


@dispatch()
def get_name(hybrid: hybrid_property) -> str:
    return hybrid.__name__


@dispatch()
def get_name(relationship: RelationshipProperty) -> str:
    return relationship.key


@dispatch()
def get_name(relationship: GenericRelationshipProperty) -> str:
    return relationship.key
