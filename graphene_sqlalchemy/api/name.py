from graphene.types.base import BaseType
from sqlalchemy import Column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import CompositeProperty, RelationshipProperty

from .field_types import OrmLike
from .namespace import dispatch


# TODO: Do we need `model` on these? At worst case, should be able to get
#       the model from the column/relationship/etc.
# NOTE: Looks like the model isn't accessible from the `Column`?
@dispatch()
def convert_name(
    orm_prop: OrmLike,
    cls: type,
    model: object,
) -> str:
    func = convert_name.dispatch(type(orm_prop), cls, type(model))
    return func(orm_prop, cls, model)


@dispatch()
def convert_name(
    orm_prop: OrmLike,
    cls: BaseType,
    model: object
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
