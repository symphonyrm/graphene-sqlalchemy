from sqlalchemy import Column, types
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import CompositeProperty, RelationshipProperty
from sqlalchemy_utils.generic import GenericRelationshipProperty

try:
    from sqlalchemy_utils import ChoiceType, JSONType, ScalarListType, TSVectorType
except ImportError:
    ChoiceType = JSONType = ScalarListType = TSVectorType = object

OrmLike = (
    Column,
    CompositeProperty,
    DeclarativeMeta,
    hybrid_property,
    RelationshipProperty,
    GenericRelationshipProperty,
)


BoolLike = (
    types.Boolean,
    mysql.types.BIT,
)


FloatLike = (
    types.Float,
    types.Numeric,
)


Int8Like = (
    mysql.types.TINYINT,
)


Int16Like = (
    types.SmallInteger,
    mysql.types.SMALLINT,
)


Int24Like = (
    mysql.types.MEDIUMINT,
)


Int32Like = (
    types.Integer,
    mysql.types.INTEGER,
)


IntLike = (
    Int8Like,
    Int16Like,
    Int24Like,
    Int32Like,
)


JSONLike = (
    types.JSON,
    postgresql.HSTORE,
    postgresql.JSON,
    postgresql.JSONB
)


StringLike = (
    types.BigInteger,
    types.Time,
    types.String,
    types.Text,
    types.Unicode,
    types.UnicodeText,
    postgresql.UUID,
    postgresql.INET,
    postgresql.CIDR,
    TSVectorType
)