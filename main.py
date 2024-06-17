import asyncio
import logging
import sys
from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from token_tg import BOT_TOKEN

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship

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
    citys: Mapped[list["UserCity"]] = relationship(back_populates='user')


class UserCity(BaseORM):
    __tablename__ = 'citys'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped["User"] = relationship(back_populates='citys')


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


class AddCityStates(StatesGroup):
    title = State()


menu_keyboard = [
    [KeyboardButton(text="Узнать погоду")],
    [KeyboardButton(text="Добавить город")],
    [KeyboardButton(text="Удалить город")],
]


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


@dp.message(AddCityStates.title)
async def handle_add_city_title(message: Message, state: FSMContext):
    with session_factory() as session:
        user = session.query(User).filter(User.tg_id == message.from_user.id).first()
        if not user:
            return
        title = message.text.capitalize()
        city = session.query(UserCity).filter(UserCity.user_id == user.id).filter(UserCity.title == title).first()
        if city:
            await message.answer("Этот город уже добавлен!")
            await state.clear()
            return
        city = UserCity(user_id=user.id, title=title)
        session.add(city)
        session.commit()
        await message.answer(f"Город {title} добавлен!")
        await state.clear()


@dp.message(F.text == 'Добавить город')
async def handle_add_city(message: Message, state: FSMContext):
    await state.set_state(AddCityStates.title)
    await message.answer("Введите название города.")


@dp.message(Command('remove_admin'))
async def handle_remove_admin(message: Message):
    with session_factory() as session:
        user = session.query(User).filter(User.tg_id == message.from_user.id).first()
        if user:
            if user.is_admin:
                user.is_admin = False
                session.commit()
                await message.answer("Вы больше не администратор!")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!\n"
                         f"Это бот для получения уведомлений о погоде.\n"
                         f"Чтобы начать пользоваться ботов добавьте ваш город.",
                         reply_markup=ReplyKeyboardMarkup(keyboard=menu_keyboard))
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
