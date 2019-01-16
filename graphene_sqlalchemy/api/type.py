from typing import Union

from graphene import ID, Boolean, Enum, Field, Float, Int, List, String, DateTime, JSONString
from graphene.types.base import BaseType

from .doc import get_doc
from .field_types import (
    BoolLike,
    ChoiceType,
    Column,
    FloatLike,
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
from .namespace import dispatch
from .nullable import is_nullable
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


@dispatch()
def convert_sqlalchemy_type(
    cls: type,
    _type: types.TypeEngine,
    column: Column
) -> None:
    func = convert_sqlalchemy_type.dispatch(cls,
                                            type(_type),
                                            type(column))
    return func(cls, _type, column)


@dispatch(object, object, object)
def convert_sqlalchemy_type(cls, _type, column):
    raise Exception(
        "Don't know how to convert the SQLAlchemy field %s for class %s with type %s (%s)"
        % (column, cls, _type, column.__class__)
    )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: StringLike,
    column: Column
) -> Union[ID, String]:
    if column.primary_key or column.foreign_keys:
        return ID(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    else:
        return String(
            description=get_doc(column),
            required=not (is_nullable(column, cls))
        )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: types.DateTime,
    column: Column
) -> DateTime:
    return DateTime(
        description=get_doc(column), required=not (is_nullable(column, cls))
    )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: Int8Like,
    column: Column
) -> Union[ID, SignedInt8, UnsignedInt8]:
    if column.primary_key or column.foreign_keys:
        return ID(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    elif getattr(type, 'unsigned', False):
        return UnsignedInt8(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    else:
        return SignedInt8(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: Int16Like,
    column: Column
) -> Union[ID, SignedInt16, UnsignedInt16]:
    if column.primary_key or column.foreign_keys:
        return ID(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    elif getattr(type, 'unsigned', False):
        return UnsignedInt16(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    else:
        return SignedInt16(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: Int24Like,
    column: Column
) -> Union[ID, SignedInt24, UnsignedInt24]:
    if column.primary_key or column.foreign_keys:
        return ID(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    elif getattr(type, 'unsigned', False):
        return UnsignedInt24(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    else:
        return SignedInt24(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: Int32Like,
    column: Column
) -> Union[ID, SignedInt32, UnsignedInt32]:
    if column.primary_key or column.foreign_keys:
        return ID(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    elif getattr(type, 'unsigned', False):
        return UnsignedInt32(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )
    else:
        return SignedInt32(
            description=get_doc(column),
            required=not (is_nullable(column, cls)),
        )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: BoolLike,
    column: Column
) -> Boolean:
    return Boolean(
        description=get_doc(column), required=not (is_nullable(column, cls))
    )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: FloatLike,
    column: Column
) -> Float:
    return Float(
        description=get_doc(column),
        required=not (is_nullable(column, cls))
    )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: types.Enum,
    column: Column
) -> Field:
    enum_class = getattr(type, 'enum_class', None)
    if enum_class:  # Check if an enum.Enum type is used
        graphene_type = Enum.from_enum(enum_class)
    else:  # Nope, just a list of string options
        items = zip(type.enums, type.enums)
        # TODO: Check if this is an ok change in logic
        # name = type.name if type.name else column.name
        graphene_type = Enum(type.name, items)
    return Field(
        graphene_type,
        description=get_doc(column),
        required=not (is_nullable(column, cls)),
    )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: ChoiceType,
    column: Column
) -> Enum:
    name = "{}_{}".format(column.table.name, column.name).upper()
    return Enum(name, type.choices, description=get_doc(column))


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: ScalarListType,
    column: Column
) -> List:
    return List(String, description=get_doc(column))


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: postgresql.ARRAY,
    column: Column
) -> List:
    graphene_type = convert_sqlalchemy_type(column.type.item_type, column)
    inner_type = type(graphene_type)
    return List(
        inner_type,
        description=get_doc(column),
        required=not (is_nullable(column, cls)),
    )


@dispatch()
def convert_sqlalchemy_type(
    cls: BaseType,
    type: JSONLike,
    column: Column
) -> JSONString:
    return JSONString(
        description=get_doc(column), required=not (is_nullable(column, cls))
    )
