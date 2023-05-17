<h2 align="center">:small_red_triangle: alchemy_graph :small_red_triangle:</h2>

![New Project](https://user-images.githubusercontent.com/68655454/236483334-a3c86f5c-f732-4465-bf78-692ddd4609b2.png)

<p align="center">
    <a href="https://pypi.python.org/pypi/alchemy_graph" alt="PyPi Package Version">
        <img src="https://img.shields.io/pypi/v/alchemy_graph.svg" /></a>
    <a href="https://pypi.python.org/pypi/alchemy_graph" alt="Supported Python versions">
        <img src="https://img.shields.io/pypi/pyversions/alchemy_graph.svg" /></a>
    <a href="https://github.com/kieled/alchemy_graph/actions/workflows/test.yml" alt="GitFlow">
        <img src="https://github.com/kieled/alchemy_graph/actions/workflows/test.yml/badge.svg" /></a>
</p>

<p align="center">SQLAlchemy mapper to Strawberry types</p>


## :pencil2: Installation
You can install mapper using pip:

```bash
pip install alchemy-graph
```

## Functions:
### `get_only_selected_fields`
Given a SQLAlchemy model class and a Strawberry Info object representing a selection set, returns a SQLAlchemy Select object that loads only the fields and relations specified in the selection set.

#### Parameters:

- sqlalchemy_class: The SQLAlchemy model class to select fields from.
- info: The Strawberry Info object representing the selection set.
- inner_selection_name: The name of an inner selection set to consider. If specified, only fields and relations under this selection set will be included in the Select object.
#### Returns:
A SQLAlchemy Select object that loads only the specified fields and relations.
### `orm_to_strawberry`
Function maps sqlalchemy model to strawberry class.

#### Parameters:
- input_data: SqlAlchemy Base Model or list of base models.
- strawberry_type: Strawberry class wrapped in strawberry.input or strawberry.type.
#### Returns:
Strawberry objects or list of them.
### `strawberry_to_dict`
Given a Strawberry object and an optional list of allowed keys, returns a dictionary representation of the object.

#### Parameters:
- `obj`: A Strawberry object to convert to a dictionary.
- `allowed_keys`: An optional list of keys to include in the output dictionary. If not specified, all keys are included.
#### Returns:
A dictionary representation of the input object.
### `orm_mapper`
Function returns decorator for your Query strawberry.field().

#### Parameters:
- `strawberry_type`: Strawberry type that should be return. Required if result_to_strawberry=True.
- `inject_query`: Inject into current function SqlAlchemy Query. Default value: False.
- `sqlalchemy_class`: SqlAlchemy model class.
- `inner_selection_name`: The name of an inner selection set to consider. If specified, only fields and relations under this selection set will be included in the Select object.
- `result_to_strawberry`: If True, it returns Strawberry object(s). Default value: True.
### `get_dict_object`
Given an SQLAlchemy object, returns a dictionary representation of the object.

#### Parameters:
- `obj`: An SQLAlchemy object to convert to a dictionary.
#### Returns:
A dictionary representation of the input object.

## LICENSE

This project is licensed under the terms of the MIT license.
