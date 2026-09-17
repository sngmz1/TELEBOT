from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from app.database.db import async_session, Order, OrderInformation, User
from app.services.catalog import SERVICES, BLOCKED_INFO_TYPES
from app.config import ADMIN_IDS
from app.keyboards.buttons import (
    info_type_kb,
    info_action_kb,
    order_confirm_kb,
    support_kb,
    back_to_menu_kb,
    admin_notification_kb,
)
from app.utils import render_menu
from datetime import datetime

router = Router()

ORDER_STATUS_LABELS = {
    "PENDING_PAYMENT": "Pending Payment",
    "PAYMENT_VERIFICATION": "Payment Verification",
    "PROCESSING": "Processing",
    "COMPLETED": "Completed",
    "CANCELLED": "Cancelled",
}
PAYMENT_STATUS_LABELS = {
    "PENDING": "Pending",
    "VERIFIED": "Verified",
    "REJECTED": "Rejected",
}


class OrderForm(StatesGroup):
    waiting_info_type = State()
    waiting_info_value = State()
    service_key = State()
    package_key = State()
    collected_info = State()


def _is_blocked_value(value: str) -> bool:
    v = value.lower()
    return any(b in v for b in BLOCKED_INFO_TYPES)


async def _gen_order_id(session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"ORD-{today}-"
    result = await session.execute(
        select(Order.order_id).where(Order.order_id.like(f"{prefix}%"))
    )
    existing = result.scalars().all()
    seq = len(existing) + 1
    return f"{prefix}{seq:04d}"


def _collect_summary(svc, pkg, collected) -> str:
    lines = []
    for i, item in enumerate(collected, 1):
        lines.append(
            f"{i}. Type: {item['type']}\n   Value: {item['value']}"
        )
    return (
        f"📋 Order Summary\n\n"
        f"🛠 Service:\n{svc['name']}\n\n"
        f"📦 Package:\n{pkg['name']}\n"
        f"Info: {len(collected)} / {pkg['max_info']}\n\n"
        f"📋 Requested Information:\n"
        + "\n".join(lines)
        + f"\n\n💰 Amount:\n{pkg['price']}\n\n"
        f"Confirm your order?"
    )


async def _notify_admins(bot, order: Order, info_list: list[dict]) -> None:
    info_lines = "\n".join(
        f"{i['type']}: {i['value']}" for i in info_list
    ) or "N/A"
    text = (
        f"🔔 NEW ORDER\n\n"
        f"Order ID:\n{order.order_id}\n\n"
        f"👤 User:\n"
        f"@{order.username or 'N/A'}\n"
        f"Telegram ID: {order.user_id}\n\n"
        f"🛠 Service:\n{order.service}\n\n"
        f"📋 Information:\n{info_lines}\n\n"
        f"📦 Package:\n{order.package}\n"
        f"Orders: {len(info_list)}\n\n"
        f"💰 Amount:\n{order.amount}\n\n"
        f"📊 Status:\n{ORDER_STATUS_LABELS.get(order.status, order.status)}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=admin_notification_kb(order.order_id))
        except Exception:
            pass


@router.callback_query(F.data == "orders")
async def cb_my_orders(callback: CallbackQuery):
    uid = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.user_id == uid).order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

    if not orders:
        await render_menu(
            callback.message,
            "📦 No orders yet.\n\nPlace an order from the 🛠 Services menu.",
            back_to_menu_kb(),
        )
        return

    lines = ["📦 Order History\n"]
    for o in orders:
        status_label = ORDER_STATUS_LABELS.get(o.status, o.status)
        lines.append(
            f"📦 {o.order_id}\n"
            f"{o.service}\n"
            f"{o.package}\n"
            f"💰 {o.amount}\n\n"
            f"Status: {status_label}\n"
            f"📅 {o.created_at.strftime('%d %b %Y')}\n"
            f"---"
        )

    await render_menu(callback.message, "\n".join(lines), back_to_menu_kb())


@router.callback_query(F.data.startswith("pkg:"))
async def cb_select_package(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    service_key, package_key = parts[1], parts[2]

    svc = SERVICES.get(service_key)
    if not svc or package_key not in svc["packages"]:
        await callback.answer("Invalid selection.", show_alert=True)
        return

    pkg = svc["packages"][package_key]

    await state.update_data(
        service_key=service_key,
        package_key=package_key,
        collected_info=[],
    )
    await state.set_state(OrderForm.waiting_info_type)

    await callback.message.edit_text(
        f"📦 {svc['name']}\n"
        f"{pkg['name']} - {pkg['price']} ({pkg['max_info']} info)\n\n"
        f"📋 Select the information type you want to provide:\n\n"
        f"Added: 0 / {pkg['max_info']}",
        reply_markup=info_type_kb(service_key, False, 0, pkg["max_info"]),
    )


@router.callback_query(F.data.startswith("info_type:"))
async def cb_info_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    service_key = data["service_key"]
    package_key = data["package_key"]
    svc = SERVICES[service_key]
    pkg = svc["packages"][package_key]

    tkey = callback.data.split(":", 1)[1]
    info_field = next((t for t in svc["info_types"] if t["key"] == tkey), None)
    if not info_field:
        await callback.answer("Invalid type.", show_alert=True)
        return

    collected = list(data.get("collected_info", []))
    if len(collected) >= pkg["max_info"]:
        await callback.answer(f"Maximum {pkg['max_info']} info allowed for this package.", show_alert=True)
        return

    await state.update_data(current_type=info_field["type"])
    await state.set_state(OrderForm.waiting_info_value)

    await callback.message.edit_text(
        f"📌 {info_field['type']}\n\n"
        f"{info_field['prompt']}\n\n"
        f"Example: {info_field['example']}",
        reply_markup=info_type_kb(service_key, len(collected) > 0, len(collected), pkg["max_info"]),
    )


@router.message(OrderForm.waiting_info_value)
async def cb_info_value(message: Message, state: FSMContext):
    value = message.text.strip()
    if len(value) < 3:
        await message.answer("⚠️ Please provide valid information (min 3 characters).")
        return

    if _is_blocked_value(value):
        await message.answer("🚫 This type of information cannot be collected. Please provide authorized information only.")
        return

    data = await state.get_data()
    service_key = data["service_key"]
    package_key = data["package_key"]
    svc = SERVICES[service_key]
    pkg = svc["packages"][package_key]

    collected = list(data.get("collected_info", []))
    info_field_type = data.get("current_type", "Info")
    collected.append({"type": info_field_type, "value": value})
    await state.update_data(collected_info=collected)

    added_lines = "\n".join(
        f"{i}. {item['type']}: {item['value']}" for i, item in enumerate(collected, 1)
    )
    remaining = pkg["max_info"] - len(collected)

    if remaining <= 0:
        await message.answer(
            _collect_summary(svc, pkg, collected),
            reply_markup=order_confirm_kb(service_key, package_key),
        )
        return

    await message.answer(
        f"✅ Information Added\n\n"
        f"{added_lines}\n\n"
        f"Added: {len(collected)} / {pkg['max_info']}\n"
        f"Remaining: {remaining}",
        reply_markup=info_action_kb(),
    )


@router.callback_query(F.data == "info_addmore")
async def cb_info_addmore(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    service_key = data["service_key"]
    svc = SERVICES[service_key]
    pkg = svc["packages"][data["package_key"]]
    collected = list(data.get("collected_info", []))

    if len(collected) >= pkg["max_info"]:
        await callback.answer(f"Maximum {pkg['max_info']} info reached.", show_alert=True)
        return

    await state.set_state(OrderForm.waiting_info_type)
    await callback.message.edit_text(
        f"📋 Select the information type:\n\n"
        f"Added: {len(collected)} / {pkg['max_info']}",
        reply_markup=info_type_kb(service_key, len(collected) > 0, len(collected), pkg["max_info"]),
    )


@router.callback_query(F.data == "info_done")
async def cb_info_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    service_key = data["service_key"]
    package_key = data["package_key"]
    svc = SERVICES[service_key]
    pkg = svc["packages"][package_key]
    collected = list(data.get("collected_info", []))

    if not collected:
        await callback.answer("Please add at least one information first.", show_alert=True)
        return

    await callback.message.edit_text(
        _collect_summary(svc, pkg, collected),
        reply_markup=order_confirm_kb(service_key, package_key),
    )


@router.callback_query(F.data.startswith("confirm:"))
async def cb_confirm_order(callback: CallbackQuery, state: FSMContext, bot):
    parts = callback.data.split(":")
    service_key, package_key = parts[1], parts[2]

    svc = SERVICES.get(service_key)
    if not svc:
        await callback.answer("Error.", show_alert=True)
        return
    pkg = svc["packages"].get(package_key)
    if not pkg:
        await callback.answer("Error.", show_alert=True)
        return

    data = await state.get_data()
    collected = data.get("collected_info", [])

    if not collected:
        await callback.answer("No information captured. Please restart the order.", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username or "",
                full_name=callback.from_user.full_name,
            )
            session.add(user)
            await session.commit()
        else:
            user.username = callback.from_user.username or user.username
            user.full_name = callback.from_user.full_name
            await session.commit()

        order_id = await _gen_order_id(session)
        order = Order(
            order_id=order_id,
            user_id=callback.from_user.id,
            username=callback.from_user.username or "",
            user_name=callback.from_user.full_name,
            service=svc["name"],
            package=pkg["name"],
            amount=pkg["price"],
            status="PENDING_PAYMENT",
            payment_status="PENDING",
        )
        session.add(order)
        await session.flush()

        for item in collected:
            session.add(OrderInformation(
                order_id=order_id,
                information_type=item["type"],
                information_value=item["value"],
            ))
        await session.commit()

        info_list = list(collected)

    await state.clear()

    await callback.message.edit_text(
        f"✅ Your order has been created.\n\n"
        f"Order ID:\n{order_id}\n\n"
        f"💰 Amount:\n{pkg['price']}\n\n"
        f"Please contact support to complete payment.",
        reply_markup=support_kb(),
    )

    await _notify_admins(bot, order, info_list)