import copy
import re
from sqlalchemy.orm import class_mapper
from strawberry.types import Info


def convert_camel_case(name: str) -> str:
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    name = pattern.sub('_', name).lower()
    return name


def find_info_in_args(*args, **kwargs) -> Info:
    if 'info' in kwargs:
        return kwargs.get('info')
    for i in args:
        if isinstance(i, Info):
            return i
    raise Exception('orm_mapper should used only with Strawberry fields')


def flatten(items):
    if not items:
        return items
    if isinstance(items[0], list):
        return flatten(items[0]) + flatten(items[1:])
    return items[:1] + flatten(items[1:])


def _to_dict(obj):
    if isinstance(obj, list) or isinstance(obj, tuple):
        return [_to_dict(i) for i in obj]
    if not hasattr(obj, '__dict__'):
        return obj
    temp = obj.__dict__
    for key, value in temp.items():
        if hasattr(value, '_enum_definition') or isinstance(value, bytes):
            continue
        elif hasattr(value, '__dict__'):
            temp[key] = _to_dict(value)
        elif isinstance(value, list):
            temp[key] = [_to_dict(i) for i in value]
    return temp


def strawberry_to_dict(
        strawberry_model,
        exclude_none: bool = False,
        exclude: set | None = None,
):
    """
    Converts a Strawberry type to a dictionary.

    :param strawberry_model: The Strawberry type to convert to dictionary.
    :param exclude_none: Whether to exclude dictionary keys with `None` values. Defaults to `False`.
    :param exclude: Set of field names to exclude from the resulting dictionary. Defaults to `None`.

    :return: A dictionary with the values of the Strawberry type.
    """
    dict_obj: dict = _to_dict(
        copy.deepcopy(strawberry_model)
    )
    result_dict = {**dict_obj}
    for k, v in dict_obj.items():
        if exclude:
            if k in exclude:
                result_dict.pop(k, None)
        if exclude_none and v is None:
            result_dict.pop(k, None)
    return result_dict


def get_dict_object(model) -> dict | list[dict]:
    """
    Map sqlalchemy model or list of them to dict

    :param model: SQLAlchemy model
    :return: dict or list of dicts
    """

    if isinstance(model, list):
        return [get_dict_object(i) for i in model]
    if isinstance(model, dict):
        for k, v in model.items():
            if isinstance(v, list):
                return {
                    **model,
                    k: [get_dict_object(i) for i in v]
                }
        return model
    mapper = class_mapper(model.__class__)
    out = {
        col.key: getattr(model, col.key)
        for col in mapper.columns
        if col.key in model.__dict__
    }
    for name, relation in mapper.relationships.items():
        if name not in model.__dict__:
            continue
        try:
            related_obj = getattr(model, name)
        except AttributeError:
            continue
        if related_obj is not None:
            if relation.uselist:
                out[name] = [get_dict_object(child) for child in related_obj]
            else:
                out[name] = get_dict_object(related_obj)
        else:
            out[name] = None
    return out
