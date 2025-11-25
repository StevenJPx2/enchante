# https://github.com/pydantic/pydantic/issues/1223
# https://github.com/pydantic/pydantic/pull/3179
# https://github.com/pydantic/pydantic/issues/1673

from copy import deepcopy
from typing import Any, Optional

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo


def optional(model: type[BaseModel]):
    def make_field_optional(
        field: FieldInfo, default: Any = None
    ) -> tuple[Any, FieldInfo]:
        new = deepcopy(field)
        if getattr(new, "default_factory", None) is None:
            new.default = default
        new.annotation = Optional[field.annotation]  # type: ignore
        return new.annotation, new

    return create_model(
        model.__name__,
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: make_field_optional(field_info)
            for field_name, field_info in model.model_fields.items()
        },
        __config__=None,
        __validators__=None,
        __doc__=None,
        __cls_kwargs__=None,
    )
