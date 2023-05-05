from sqlalchemy import Column, Integer, String, ForeignKey, Select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import strawberry
from strawberry.types import Info

from alchemy_graph import get_only_selected_fields, orm_to_strawberry, orm_mapper

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)

    posts = relationship("Post", back_populates="user")


class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(String)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", back_populates="posts")


@strawberry.type
class UserType:
    id: int
    name: str
    email: str
    posts: list['PostType']


@strawberry.type
class PostType:
    id: int
    title: str
    body: str
    user: 'UserType'


@strawberry.type
class Query:
    @orm_mapper(UserType, inject_query=True, sqlalchemy_class=User)
    @strawberry.field
    def user(self, query: Select, user_id: int) -> UserType:
        user: User = query.where(User.id == user_id).first()

        if not user:
            raise ValueError(f"No user with id {user_id} found")

        return user

    @strawberry.field
    def users(self, info: Info, limit: int = 10, offset: int = 0) -> list[UserType]:
        query = get_only_selected_fields(User, info)
        users = query.limit(limit).offset(offset).all()

        return orm_to_strawberry(users, UserType)

    @strawberry.field
    def post(self, info: Info, post_id: int) -> PostType:
        query = get_only_selected_fields(Post, info)
        post = query.filter(Post.id == post_id).first()

        if not post:
            raise ValueError(f"No post with id {post_id} found")

        return orm_to_strawberry(post, PostType)

    @orm_mapper(PostType, inject_query=True, sqlalchemy_class=Post)
    @strawberry.field
    def posts(self, query: Select, limit: int = 10, offset: int = 0) -> list[PostType]:
        posts: list[Post] = query.limit(limit).offset(offset).all()
        return posts


schema = strawberry.Schema(query=Query, types=[UserType, PostType])
