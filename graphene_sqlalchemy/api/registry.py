from graphene.types.base import BaseType
from sqlalchemy.ext.declarative.api import DeclarativeMeta

from .name import convert_name
from .namespace import dispatch, get_registry

@dispatch()
def set_registry_class(cls: type):
    func = set_registry_class.dispatch(cls)
    return func(cls)


def generate_type(_super: BaseType, model: DeclarativeMeta):
    meta = {
        'Meta': {
            'model': model
        }
    }
    registry = get_registry(_super)
    _class = registry.get_type_for_model(model)

    return _class or type(
        convert_name(_super, model),
        (_super,),
        meta
    )
