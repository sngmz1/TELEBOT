from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from app.services.catalog import SERVICES
from app.keyboards.buttons import services_kb, package_kb
from app.utils import render_menu

router = Router()


@router.callback_query(F.data == "services")
async def cb_services(callback: CallbackQuery):
    await render_menu(
        callback.message,
        "🛠 Our Services\n\nSelect a service:",
        services_kb(),
    )


@router.callback_query(F.data.startswith("svc:"))
async def cb_service_select(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    svc = SERVICES.get(key)
    if not svc:
        await callback.answer("Service not found.", show_alert=True)
        return

    await callback.message.edit_text(
        "📦 Select a package:",
        reply_markup=package_kb(key),
    )
