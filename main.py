import asyncio
from datetime import datetime
from random import shuffle

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column


DB_DIALECT = "postgresql+psycopg2"
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "postgres"
BOT_TOKEN = ""


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


dp = Dispatcher()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))


def write_user_message(message: Message):
    with session_factory() as session:
        msg_log = MessageLog(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            text=message.text,
            timestamp=message.date
        )
        session.add(msg_log)
        session.commit()


def write_bot_message(message: Message, text: str):
    with session_factory() as session:
        msg_log = MessageLog(
            user_id=None,
            chat_id=message.chat.id,
            text=text,
            timestamp=datetime.now(),
        )
        session.add(msg_log)
        session.commit()


@dp.message()
async def handle_message(message: Message):
    write_user_message(message)
    user_text = message.text.split()
    shuffle(user_text)
    bot_text = " ".join(user_text).title()
    await message.answer(bot_text)
    write_bot_message(message, bot_text)


async def main():
    with session_factory() as session:
        Base.metadata.create_all(engine)
        session.commit()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
