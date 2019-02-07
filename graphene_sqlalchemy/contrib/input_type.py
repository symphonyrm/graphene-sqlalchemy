import graphene

from graphene.types.utils import yank_fields_from_attrs

from ..types import SQLAlchemyObjectTypeOptions
from ..api import construct_fields, dispatch, get_registry, set_registry_class
from ..utils import check_mapped_class


class SQLAlchemyInputObjectType(graphene.InputObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, model=None, _meta=None,
                                    skip_registry=False, **options):
        """Initializes an input object type based on a sqlalchemy model."""
        check_mapped_class(model)

        # Provide defaults for optional arguments.
        _meta = _meta or SQLAlchemyObjectTypeOptions(cls)
        _meta.model = model
        _meta.fields = _meta.fields or {}

        # Automatically construct GraphQL fields from the SQLAlchemy model.
        # _meta.fields.update(
        yank_fields_from_attrs(
            construct_fields(cls, model),
            _as=graphene.Field)#)

        super(SQLAlchemyInputObjectType,
              cls).__init_subclass_with_meta__(_meta=_meta, **options)

        if not skip_registry:
            registry = get_registry(set_registry_class(cls))
            registry.register(cls)


@dispatch()
def set_registry_class(cls: SQLAlchemyInputObjectType):
    return SQLAlchemyInputObjectType
