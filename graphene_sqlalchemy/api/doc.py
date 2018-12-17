from sqlalchemy import Column

from .namespace import dispatch


@dispatch()
def get_doc(column: Column):
    return getattr(column, "doc", None)
