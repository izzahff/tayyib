from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from tayyib.config import settings

engine = create_engine(settings.database_url)


def get_session() -> Session:
    return Session(engine)


def create_db_and_tables() -> None:
    from tayyib.storage import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
