from enum import Enum as PyEnum
from functools import partial
from typing import Union

from graphene import ID, Boolean, Enum, Field, Float, Int, List, String, DateTime, JSONString
from graphene.types.base import BaseType
from sqlalchemy import inspect
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import CompositeProperty

from .field_types import (
    BoolLike,
    ChoiceType,
    Column,
    FloatLike,
    IntLike,
    Int8Like,
    Int16Like,
    Int24Like,
    Int32Like,
    JSONLike,
    postgresql,
    ScalarListType,
    StringLike,
    types,
)
from .namespace import dispatch, get_registry
from ..scalars import (
    SignedInt8,
    SignedInt16,
    SignedInt24,
    SignedInt32,
    UnsignedInt8,
    UnsignedInt16,
    UnsignedInt24,
    UnsignedInt32,
)
from ..utils import is_generic_key


def is_key(model: DeclarativeMeta, column: Column) -> bool:
    return column.primary_key or column.foreign_keys or is_generic_key(model, column)


def is_unsigned(type: IntLike) -> bool:
    return getattr(type, 'unsigned', False)


@dispatch()
def convert_type(
    cls: type,
    model: DeclarativeMeta,
    composite: CompositeProperty,
) -> None:
    func = convert_composite_class.dispatch(cls, type(composite))
    return func(cls, _type, column)


@dispatch()
def convert_type(
    cls: type,
    model: DeclarativeMeta,
    column: Column,
    _type: types.TypeEngine,
) -> None:
    func = convert_type.dispatch(cls, type(model), type(column), type(_type))
    return func(cls, model, column, _type)


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: StringLike,
) -> Union[ID, String]:
    if is_key(model, column):
        return ID
    return String


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: types.DateTime,
) -> DateTime:
    return DateTime


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: Int8Like,
) -> Union[ID, SignedInt8, UnsignedInt8]:
    if is_key(model, column):
        return ID
    elif is_unsigned(_type):
        return UnsignedInt8
    else:
        return SignedInt8


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: Int16Like,
) -> Union[ID, SignedInt16, UnsignedInt16]:
    if is_key(model, column):
        return ID
    elif is_unsigned(_type):
        return UnsignedInt16
    else:
        return SignedInt16


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: Int24Like,
) -> Union[ID, SignedInt24, UnsignedInt24]:
    if is_key(model, column):
        return ID
    elif is_unsigned(_type):
        return UnsignedInt24
    else:
        return SignedInt24


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: Int32Like,
) -> Union[ID, SignedInt32, UnsignedInt32]:
    if is_key(model, column):
        return ID
    elif is_unsigned(_type):
        return UnsignedInt32
    else:
        return SignedInt32


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: BoolLike,
) -> Boolean:
    return Boolean


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: FloatLike,
) -> Float:
    return Float


@dispatch()
def convert_enum():
    raise NotImplementedError()


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: types.Enum,
) -> Field:
    prefix = _type.name if _type.name else column.name
    name = "{}_enum".format(prefix)
    enum_class = getattr(_type, 'enum_class')
    if not enum_class:
        enum_class = PyEnum(name, _type.enums)

    try:
        func = convert_enum.dispatch(type(enum_class))
        graphene_type = func(enum_class)
    except:
        graphene_type = Enum.from_enum(enum_class)
        convert_enum.add((type(enum_class),), lambda e: graphene_type)

    return partial(Field, graphene_type)


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: ChoiceType,
) -> Enum:
    name = "{}_{}".format(column.table.name, column.name).upper()
    return partial(Enum, name, _type.choices)


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: ScalarListType,
) -> List:
    return partial(List, String)


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: postgresql.ARRAY,
) -> List:
    inner_type = convert_type(cls, _type.item_type, column)
    return partial(List, inner_type)


@dispatch()
def convert_type(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
    _type: JSONLike,
) -> JSONLike:
    return JSONString
