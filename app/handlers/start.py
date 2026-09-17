from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.config import REQUIRED_CHANNEL_USERNAME
from app.keyboards.buttons import channel_check_kb, main_menu_kb
from app.database.db import async_session, User
from app.utils import render_menu
from sqlalchemy import select

from pathlib import Path

router = Router()

WELCOME_IMG = Path(__file__).resolve().parents[2] / "IMAGE" / "photo_6151986094392677145_w.jpg"

WELCOME_TEXT = "👋 Welcome!\n\nChoose an option below:"


def _is_member(member) -> bool:
    return member.status in ("member", "administrator", "creator")


async def _save_user(user) -> None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user.id))
        existing = result.scalar_one_or_none()
        if not existing:
            session.add(User(
                telegram_id=user.id,
                username=user.username or "",
                full_name=user.full_name,
            ))
            await session.commit()
        else:
            existing.username = user.username or existing.username
            existing.full_name = user.full_name
            await session.commit()


@router.message(F.text == "/start")
async def cmd_start(message: Message, bot):
    await _save_user(message.from_user)
    try:
        member = await bot.get_chat_member(f"@{REQUIRED_CHANNEL_USERNAME}", message.from_user.id)
        if _is_member(member):
            await message.answer_photo(
                FSInputFile(WELCOME_IMG),
                caption=WELCOME_TEXT,
                reply_markup=main_menu_kb(),
            )
        else:
            await message.answer(
                "📢 Please join our channel to use this bot.",
                reply_markup=channel_check_kb(),
            )
    except Exception:
        await message.answer(
            "📢 Please join our channel to use this bot.",
            reply_markup=channel_check_kb(),
        )


@router.callback_query(F.data == "check_channel")
async def cb_check_channel(callback: CallbackQuery, bot):
    try:
        member = await bot.get_chat_member(f"@{REQUIRED_CHANNEL_USERNAME}", callback.from_user.id)
        if _is_member(member):
            await callback.message.delete()
            await callback.message.answer_photo(
                FSInputFile(WELCOME_IMG),
                caption=WELCOME_TEXT,
                reply_markup=main_menu_kb(),
            )
        else:
            await callback.answer("❌ You haven't joined yet.", show_alert=True)
    except Exception:
        await callback.answer("❌ Could not verify. Try again.", show_alert=True)


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await render_menu(
        callback.message,
        "👋 Welcome!\n\nChoose an option below:",
        main_menu_kb(),
    )