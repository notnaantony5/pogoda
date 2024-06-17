import asyncio
import logging
import sys
from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from token_tg import BOT_TOKEN

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column

ADMIN_PASSWORD = "12431243"

class BaseORM(DeclarativeBase):
    __abstract__ = True
class User(BaseORM):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(unique=True)
    fullname: Mapped[str]
    created_at: Mapped[datetime]
    is_admin: Mapped[bool] = mapped_column(default=False)


def db_setup():
    db_engine = create_engine("sqlite:///db.sqlite3")
    db_session_factory = sessionmaker(bind=db_engine)
    with db_session_factory() as session:
        BaseORM.metadata.create_all(db_engine)
        session.commit()
    return db_engine, db_session_factory

engine, session_factory = db_setup()

dp = Dispatcher()

class AdminSign(StatesGroup):
    password = State()

@dp.message(AdminSign.password)
async def handle_password(message: Message, state: FSMContext):
    if ADMIN_PASSWORD == message.text:
        with session_factory() as session:
            user = session.query(User).filter(User.tg_id == message.from_user.id).first()
            if user:
                user.is_admin = True
                session.commit()
                await message.answer("Вы теперь администратор!")
    else:
        await message.answer("Неверный пароль!")
    await state.clear()


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

@dp.message(Command('admin'))
async def admin_handler(message: Message, state: FSMContext) -> None:
    with session_factory() as session:
        user = session.query(User).filter(User.tg_id == message.from_user.id).first()
        if not user:
            return
        if user.is_admin:
            await message.answer("Вы уже администратор!")
            return
        await state.set_state(AdminSign.password)
        await message.answer("Введите админский пароль!")





async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


