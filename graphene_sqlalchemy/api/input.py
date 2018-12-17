from datetime import datetime
from graphene.types.base import BaseType
from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import RelationshipProperty

from .field_types import OrmLike
from .name import get_name, convert_name
from .namespace import dispatch
from .orm import order_orm_properties


PrimitiveLike = (bool, datetime, float, int, str, type(None))


@dispatch()
def convert_to_instance(
    model: DeclarativeMeta,
    inputs: BaseType
): # TODO: Add return type
    orm_prop_list = [
        (get_name(orm_prop), convert_name(orm_prop, inputs, model), orm_prop)
        for orm_prop in order_orm_properties(model)
        if convert_name(orm_prop, inputs, model) in inputs
    ]

    return model(**{
        name: convert_to_instance(orm_prop, inputs[input_name])
        for name, input_name, orm_prop in orm_prop_list
    })


@dispatch()
def convert_to_instance(
    column: Column,
    inputs: PrimitiveLike
) -> PrimitiveLike:
    return inputs


@dispatch()
def convert_to_instance(
    relationship: RelationshipProperty,
    inputs: BaseType
):# -> Base:
    return convert_to_instance(relationship.mapper.entity, inputs)


@dispatch()
def convert_to_instance(
    relationship: RelationshipProperty,
    inputs: list
):# -> Base:
    return [
        convert_to_instance(relationship.mapper.entity, item)
        for item in inputs
    ]
