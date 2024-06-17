import asyncio
import logging
import sys
from datetime import datetime
from token_tg import BOT_TOKEN

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column

class BaseORM(DeclarativeBase):
    __abstract__ = True
class User(BaseORM):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(unique=True)
    fullname: Mapped[str]
    created_at: Mapped[datetime]


def db_setup():
    db_engine = create_engine("sqlite:///db.sqlite3")
    db_session_factory = sessionmaker(bind=db_engine)
    with db_session_factory() as session:
        BaseORM.metadata.create_all(db_engine)
        session.commit()
    return db_engine, db_session_factory

engine, session_factory = db_setup()

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!\n"
                         f"Это бот для получения уведомлений о погоде.\n"
                         f"Чтобы начать пользоваться ботов добавьте ваш город.")
    with session_factory() as session:
        tg_user = message.from_user
        if session.query(User).filter(User.tg_id == tg_user.id).first():
            return
        user = User(tg_id=tg_user.id, username=tg_user.username, fullname=tg_user.full_name, created_at=datetime.now())
        session.add(user)
        session.commit()

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


