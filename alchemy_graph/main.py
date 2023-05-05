import enum
from datetime import datetime
from functools import wraps
from types import GenericAlias, UnionType

import strawberry
from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload, load_only
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.types import Info
from strawberry.types.nodes import SelectedField

from .utils import (
    convert_camel_case,
    find_info_in_args,
    flatten,
    get_dict_object,
    strawberry_to_dict,
)


def get_relation_options(relation: dict, prev_sql: Select | None = None):
    key, val = next(iter(relation.items()))
    fields = val["fields"]
    relations = val["relations"]
    if prev_sql:
        sql = prev_sql.joinedload(key).load_only(*fields)
    else:
        sql = joinedload(key).load_only(*fields)
    if len(relations) == 0:
        yield sql
    if len(relations) == 1:
        yield from get_relation_options(relations[0], sql)
    for i in relations:
        rels = get_relation_options(i, sql)
        if hasattr(rels, "__iter__"):
            yield from rels
        else:
            yield rels


def get_only_selected_fields(
    sqlalchemy_class, info: Info, inner_selection_name: str | None = None
) -> Select:
    """Given a SQLAlchemy model class and a Strawberry `Info` object representing a selection set,
    returns a SQLAlchemy `Select` object that loads only the fields and relations specified in the selection set.

    :param sqlalchemy_class: The SQLAlchemy model class to select fields from.
    :param info: The Strawberry `Info` object representing the selection set.
    :param inner_selection_name: The name of an inner selection set to consider. If specified, only fields and relations under this selection set will be included in the `Select` object.

    :return: A SQLAlchemy `Select` object that loads only the specified fields and relations.
    """

    def process_items(items: list[SelectedField], db_class):
        current_fields, relations = [], []
        for item in items:
            if item.name == "__typename":
                continue
            try:
                relation_name = getattr(db_class, convert_camel_case(item.name))
            except AttributeError:
                continue
            if not len(item.selections):
                current_fields.append(relation_name)
                continue
            related_class = relation_name.property.mapper.class_
            relations.append(
                {relation_name: process_items(item.selections, related_class)}
            )
        return {"fields": current_fields, "relations": relations}

    selections = info.selected_fields[0].selections
    if inner_selection_name:
        try:
            selections = next(
                sel for sel in selections if sel.name == inner_selection_name
            ).selections
        except ValueError:
            pass
    options = process_items(selections, sqlalchemy_class)

    fields = [load_only(*options["fields"])] if len(options["fields"]) else []

    query_options = [
        *fields,
        *flatten([list(get_relation_options(i)) for i in options["relations"]]),
    ]

    return select(sqlalchemy_class).options(*query_options)


def _orm_to_strawberry_step(item: dict, current_strawberry_type):
    annots = current_strawberry_type.__annotations__
    temp = {}
    for k, v in item.items():
        if k not in annots.keys():
            continue
        current_type = annots.get(k)
        if isinstance(v, (str, int, float, datetime)):
            temp[k] = v
            continue
        if isinstance(v, enum.Enum):
            temp[k] = strawberry.enum(v.__class__)[v.value]
            continue
        if isinstance(current_type, StrawberryOptional):
            current_type = current_type.of_type
        if isinstance(current_type, UnionType):
            current_type = [i for i in current_type.__args__ if i is not None][0]
        if isinstance(current_type, StrawberryList):
            current_type = current_type.of_type
        if isinstance(current_type, GenericAlias):
            current_type = current_type.__args__[0]
        if isinstance(v, list):
            temp[k] = [_orm_to_strawberry_step(i, current_type) for i in item[k]]
        elif isinstance(v, dict):
            temp[k] = _orm_to_strawberry_step(item[k], current_type)
    return current_strawberry_type(**temp)


def orm_to_strawberry(input_data, strawberry_type):
    """
    Function maps sqlalchemy model to strawberry class

    :param input_data: SqlAlchemy Base Model or list of base models
    :param strawberry_type: Strawberry class wrapped in `strawberry.input` or `strawberry.type`
    :return: Strawberry objects or list of them
    """

    if isinstance(input_data, list):
        return [
            _orm_to_strawberry_step(get_dict_object(item), strawberry_type)
            for item in input_data
        ]
    return _orm_to_strawberry_step(get_dict_object(input_data), strawberry_type)


def orm_mapper(
    strawberry_type=None,
    *,
    inject_query: bool = False,
    sqlalchemy_class=None,
    inner_selection_name: str | None = None,
    result_to_strawberry: bool = True
):
    """
    Function returns decorator for your Query strawberry.field()

    :param strawberry_type: Strawberry type that should be return. Required if `result_to_strawberry=True`
    :param inject_query: Inject into current function SQLAlchemy select expression based on the GraphQL query
    :param sqlalchemy_class: If inject_query is true is required. Create select expression for your sqlalchemy Base model
    :param inner_selection_name: If you have GraphQL query like `{"items": SomeType[], "count": 10} and you only need items - type items in this param`
    :param result_to_strawberry: Default `True`. If True map result from sqlalchemy to strawberry class
    :return: decorator
    """

    def decorator(func: callable) -> callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if inject_query:
                if not sqlalchemy_class:
                    raise Exception(
                        "Sqlalchemy class is required when using inject_query=True"
                    )
                query = get_only_selected_fields(
                    sqlalchemy_class,
                    find_info_in_args(*args, **kwargs),
                    inner_selection_name,
                )
                result = func(query, *args, **kwargs)
            else:
                result = func(*args, **kwargs)
            if result_to_strawberry:
                return orm_to_strawberry(result, strawberry_type)
            return result

        return wrapper

    return decorator


__all__ = [
    "orm_to_strawberry",
    "get_only_selected_fields",
    "strawberry_to_dict",
    "orm_mapper",
    "get_dict_object",
]
