from sqlalchemy import Column, types
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import CompositeProperty, RelationshipProperty
try:
    from sqlalchemy_utils import ChoiceType, JSONType, ScalarListType, TSVectorType
except ImportError:
    ChoiceType = JSONType = ScalarListType = TSVectorType = object

OrmLike = (
    Column,
    CompositeProperty,
    hybrid_property,
    RelationshipProperty,
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


JSONLike = (
    JSONType,
    postgresql.HSTORE,
    postgresql.JSON,
    postgresql.JSONB
)


StringLike = (
    types.BigInteger,
    types.Date,
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