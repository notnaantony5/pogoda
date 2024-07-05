from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column

DB_DIALECT = "postgresql+psycopg2"
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "postgres"

engine = create_engine(f"{DB_DIALECT}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

session_factory = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    """Базовая модель."""

class MessageLog(Base):
    __tablename__ = "message_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None]
    chat_id: Mapped[int]
    text: Mapped[str]
    timestamp: Mapped[datetime]



def main():
    with session_factory() as session:
        Base.metadata.create_all(engine)
        session.commit()