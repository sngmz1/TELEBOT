from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.keyboards.buttons import more_kb, back_to_menu_kb
from app.utils import render_menu

router = Router()


@router.callback_query(F.data == "more")
async def cb_more(callback: CallbackQuery):
    await render_menu(callback.message, "➕ More", more_kb())


@router.callback_query(F.data == "tnc")
async def cb_tnc(callback: CallbackQuery):
    await render_menu(
        callback.message,
        "📜 Terms & Conditions\n\n"
        "1. Services are for informational purposes only.\n"
        "2. We do not guarantee outcomes.\n"
        "3. Payments are non-refundable once service begins.\n"
        "4. You must be 18+ to use this bot.\n"
        "5. We reserve the right to refuse service.",
        more_kb(),
    )


@router.callback_query(F.data == "privacy")
async def cb_privacy(callback: CallbackQuery):
    await render_menu(
        callback.message,
        "🔐 Privacy Policy\n\n"
        "We only collect your Telegram ID, name, and username.\n"
        "We do not share your data with third parties.\n"
        "We do not store payment credentials.\n"
        "Contact support to request data deletion.",
        more_kb(),
    )


@router.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery):
    await render_menu(
        callback.message,
        "ℹ️ About\n\n"
        "This is an automated order management bot.\n"
        "Select a service, place an order, and contact support for payment.\n\n"
        "For help, contact @HL_SKULK",
        more_kb(),
    )
