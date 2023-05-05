import enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

from alchemy_graph.utils import (
    strawberry_to_dict,
    convert_camel_case,
    get_dict_object
)
import strawberry


def test_convert_camel_case():
    assert convert_camel_case('CamelCaseTest') == 'camel_case_test'
    assert convert_camel_case('testCamelCase') == 'test_camel_case'
    assert convert_camel_case('Test') == 'test'
    assert convert_camel_case('TestNameSpace') == 'test_name_space'


def test_strawberry_to_dict():
    @strawberry.enum
    class TestEnum(enum.Enum):
        a = 'a'
        b = 'b'

    @strawberry.type
    class MyObject:
        foo: str
        bar: int
        baz: float
        enum_value: TestEnum

    my_obj = MyObject(foo="hello", bar=42, baz=3.14, enum_value=TestEnum.a)

    expected_dict = {
        "foo": "hello",
        "bar": 42,
        "baz": 3.14,
        "enum_value": TestEnum.a,
    }
    assert strawberry_to_dict(my_obj) == expected_dict

    assert strawberry_to_dict(my_obj, exclude_none=True) == expected_dict

    expected_dict = {
        "foo": "hello",
        "bar": 42,
        "enum_value": TestEnum.a,
    }

    assert strawberry_to_dict(my_obj, exclude={"baz"}) == expected_dict

    @strawberry.type
    class NestedObject:
        items: list[int]

    @strawberry.type
    class MyObjectWithList:
        foo: list[int]
        nested: NestedObject

    my_obj_with_list = MyObjectWithList(foo=[1, 2, 3], nested=NestedObject(items=[4, 5, 6]))

    expected_dict = {
        "foo": [1, 2, 3],
        "nested": {"items": [4, 5, 6]},
    }
    assert strawberry_to_dict(my_obj_with_list) == expected_dict


def test_get_dict_object():
    Base = declarative_base()

    class TestAddress(Base):
        __tablename__ = 'test_address'

        id: Mapped[int] = mapped_column(primary_key=True)
        street: Mapped[str]
        city: Mapped[str]

    class TestObj(Base):
        __tablename__ = 'test_obj'

        id: Mapped[int] = mapped_column(primary_key=True)
        age: Mapped[int]
        name: Mapped[str]
        address_id: Mapped[int] = mapped_column(ForeignKey('test_address.id'))

        address: Mapped[TestAddress] = relationship()

    result_dict = {"id": 1, "name": "Alice", "age": 30, "address": {"id": 1, "street": "123 Main St", "city": "Anytown"}}

    test_instance = TestObj(
        id=1,
        age=30,
        name='Alice',
        address=TestAddress(
            id=1,
            street='123 Main St',
            city='Anytown'
        )
    )

    assert get_dict_object(test_instance) == result_dict
