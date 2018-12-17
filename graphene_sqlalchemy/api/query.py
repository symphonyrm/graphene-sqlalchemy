from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import Query

from .namespace import dispatch


@dispatch()
def convert_to_query(
    model: DeclarativeMeta,
    query: Query,
    filters: dict
) -> Query:
    return query

