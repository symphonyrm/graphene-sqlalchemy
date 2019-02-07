from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import Query

from .namespace import dispatch


@dispatch()
def convert_to_query(
    filters: dict,
    model: DeclarativeMeta,
    query: Query
) -> Query:
    return query

