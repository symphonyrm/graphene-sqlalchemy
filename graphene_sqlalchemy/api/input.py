from datetime import datetime
from graphene.types.base import BaseType
from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import RelationshipProperty, Session
from sqlalchemy_utils.generic import GenericRelationshipProperty

from .field_types import OrmLike
from .name import get_name, convert_name
from .namespace import dispatch
from .orm import order_orm_properties


PrimitiveLike = (bool, datetime, float, int, str, type(None))


# TODO: See if we can clean this up substantially
#
#       Change the model/instance types from object. See if we can unify
#       the model/instance more easily.
#
#       Flesh out return types?
@dispatch()
def convert_to_instance(
    inputs: BaseType,
    model: DeclarativeMeta,
    session: Session
):
    orm_prop_list = order_orm_properties(model)
    instance = model()

    for orm_prop in orm_prop_list:
        instance = convert_to_instance(inputs, instance, orm_prop, session)
    return instance


@dispatch()
def convert_to_instance(
    inputs: BaseType,
    instance: object,
    column: Column,
    session: Session
):
    input_name = convert_name(inputs, inputs._meta.model, column)
    if input_name in inputs.keys():
        setattr(instance, column.name, inputs[input_name])

    return instance


@dispatch()
def convert_to_instance(
    inputs: BaseType,
    instance: object,
    relationship: RelationshipProperty,
    session: Session
):
    input_name = convert_name(inputs, inputs._meta.model, relationship)
    if input_name in inputs.keys():
        setattr(
            instance,
            relationship.key,
            convert_to_instance(inputs[input_name], relationship.mapper.entity, session)
        )

    return instance


@dispatch()
def convert_to_instance(
    inputs: list,
    model: DeclarativeMeta,
    session: Session
):
    return [
        convert_to_instance(item, model, session)
        for item in inputs
    ]


@dispatch()
def convert_to_instance(
    inputs: list,
    instance: object,
    relationship: RelationshipProperty,
    session: Session
):
    input_name = convert_name(inputs, inputs._meta.model, relationship)
    if input_name in inputs.keys():
        value = [
            convert_to_instance(item, relationship.mapper.entity, session)
            for item in inputs
        ]

        setattr(instance, relationship.key, value)

    return instance


@dispatch()
def convert_to_instance(
    inputs: BaseType,
    instance: object,
    relationship: GenericRelationshipProperty,
    session: Session
):
    return instance
