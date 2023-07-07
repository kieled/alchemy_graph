from typing import Type, TypeVar

from sqlalchemy.orm import DeclarativeBase

AL = TypeVar("AL", bound=DeclarativeBase)
T = TypeVar("T", bound=Type)
F = TypeVar("F")
