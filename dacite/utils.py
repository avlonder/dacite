from dataclasses import Field, is_dataclass
from typing import Any, Generic, TypeVar, get_args, get_origin, get_type_hints

from .dataclasses import get_fields


def _add_generics(type_origin: Any, type_args: tuple, generics: dict) -> None:
    """Adds (type var, concrete type) entries derived from a type's origin and args to the provided generics dict."""
    if type_origin and type_args and hasattr(type_origin, '__parameters__'):
        for param, arg in zip(type_origin.__parameters__, type_args):
            if param.__class__ is TypeVar:
                if param in generics and generics[param] != arg:
                    raise Exception('Generics error.')
                generics[param] = arg


def _concretize(hint: type, generics: dict[type, type]) -> type:
    """Recursively replace type vars by concrete types."""
    if hint.__class__ is TypeVar:
        return generics.get(hint, hint)
    hint_origin = get_origin(hint)
    hint_args = get_args(hint)
    if hint_origin and hint_args:
        concrete_hint_args = tuple(_concretize(a, generics) for a in hint_args)
        return hint_origin[concrete_hint_args]
    return hint


def _orig(data_class: type) -> Any:
    # NOTE Page[Entity] is not recognized as dataclass even though both Page and Entity are dataclasses
    if is_dataclass(data_class):
        return data_class
    return get_origin(data_class)


def my_get_type_hints(data_class: type, *args, **kwargs) -> dict[str, Any]:
    """
    An overwrite of dacite's get_type_hints function, supporting generics,
    i.e. substituting concrete types in type vars.
    """
    generics = {}

    dc_origin = get_origin(data_class)
    dc_args = get_args(data_class)
    _add_generics(dc_origin, dc_args, generics)

    if hasattr(data_class, '__orig_bases__'):
        for base in data_class.__orig_bases__:
            base_origin = get_origin(base)
            base_args = get_args(base)
            if base_origin is not Generic:
                _add_generics(base_origin, base_args, generics)

    hints = get_type_hints(_orig(data_class), *args, **kwargs)

    for key, hint in hints.copy().items():
        hints[key] = _concretize(hint, generics)

    return hints


def my_get_fields(data_class: type) -> list[Field]:
    """An overwrite of dacite's get_fields function, supporting generics."""
    return get_fields(_orig(data_class))
