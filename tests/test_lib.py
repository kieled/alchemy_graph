import os

import pytest
import strawberry
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from strawberry.fastapi import GraphQLRouter
from strawberry.schema.config import StrawberryConfig
from strawberry.types import Info

from alchemy_graph import get_only_selected_fields, orm_to_strawberry

Base = declarative_base()

engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str]


app = FastAPI()


@strawberry.type
class TestType:
    id: int
    value: str


@strawberry.type
class Query:
    @strawberry.field
    async def test_list(self, info: Info) -> list[TestType]:
        query = get_only_selected_fields(Test, info)
        async with async_session() as s:
            db_items = (await s.scalars(query)).all()
        return orm_to_strawberry(db_items, TestType)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_test(self, value: str) -> TestType:
        async with async_session() as s:
            await s.execute(insert(Test).values(value=value))
            await s.commit()
            instance = (await s.scalars(select(Test))).first()
        return orm_to_strawberry(instance, TestType)


strawberry_config = StrawberryConfig(auto_camel_case=True)
schema = strawberry.Schema(Query, Mutation, config=strawberry_config)
router = GraphQLRouter(schema, graphiql=False)

app.include_router(router, prefix="/graphql")

client = TestClient(app)


@pytest.fixture
def db():
    Base.metadata.create_all(create_engine("sqlite:///./test.db"))
    yield
    os.remove("./test.db")


def test_create_instance(db):
    response = client.post(
        "/graphql",
        json={"query": 'mutation { createTest(value:"test") { id, value } }'},
    )
    assert response.status_code == 200
    assert response.json() == {"data": {"createTest": {"id": 1, "value": "test"}}}


def test_retrieve_list(db):
    for _i in range(3):
        client.post(
            "/graphql", json={"query": 'mutation { createTest(value:"test") { id } }'}
        )
    response = client.post("/graphql", json={"query": "{ testList { id, value } }"})
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "testList": [
                {"id": 1, "value": "test"},
                {"id": 2, "value": "test"},
                {"id": 3, "value": "test"},
            ]
        }
    }
