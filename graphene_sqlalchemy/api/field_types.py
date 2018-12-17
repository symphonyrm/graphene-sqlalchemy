from sqlalchemy import Column, types
from sqlalchemy.dialects import postgresql
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


FloatLike = (
    types.Float,
    types.Numeric,
    types.BigInteger
)


IntLike = (
    types.SmallInteger,
    types.Integer
)


JSONLike = (
    JSONType,
    postgresql.HSTORE,
    postgresql.JSON,
    postgresql.JSONB
)


StringLike = (
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