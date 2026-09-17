from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.config import ADMIN_IDS
from app.database.db import async_session, Order, OrderInformation
from app.keyboards.buttons import (
    admin_panel_kb,
    admin_orders_kb,
    admin_orders_list_kb,
    admin_search_kb,
)
from sqlalchemy import select, or_
from aiogram.filters import Command

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


class AdminSearch(StatesGroup):
    waiting_query = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def _get_order_full(session, order: Order) -> str:
    result = await session.execute(
        select(OrderInformation).where(OrderInformation.order_id == order.order_id)
    )
    info_rows = result.scalars().all()

    info_lines = []
    if info_rows:
        for i, row in enumerate(info_rows, 1):
            info_lines.append(
                f"{i}. Type: {row.information_type}\n   Value: {row.information_value}"
            )
    else:
        info_lines.append("N/A")

    status_label = ORDER_STATUS_LABELS.get(order.status, order.status)
    payment_label = PAYMENT_STATUS_LABELS.get(order.payment_status, order.payment_status)
    created = order.created_at.strftime("%d %b %Y, %H:%M")
    info_count = len(info_rows)

    return (
        "━━━━━━━━━━━━━━━━\n"
        "📦 ORDER DETAILS\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"Order ID:\n{order.order_id}\n\n"
        "👤 USER\n\n"
        f"Name:\n{order.user_name}\n"
        f"Username:\n@{order.username or 'N/A'}\n"
        f"Telegram ID:\n{order.user_id}\n\n"
        "🛠 SERVICE\n\n"
        f"Category:\n{order.service}\n\n"
        "📋 REQUESTED INFORMATION\n\n"
        + "\n".join(info_lines)
        + "\n\n"
        "📦 PACKAGE\n\n"
        f"{order.package}\n"
        f"Orders: {info_count}\n\n"
        "💰 AMOUNT\n\n"
        f"{order.amount}\n\n"
        "📊 STATUS\n\n"
        f"Order:\n{status_label}\n"
        f"Payment:\n{payment_label}\n\n"
        "⏰ CREATED\n\n"
        f"{created}\n"
        "━━━━━━━━━━━━━━━━"
    )


async def _send_user_update(user_id: int, text: str, bot) -> None:
    try:
        await bot.send_message(user_id, text)
    except Exception:
        pass


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ You are not authorized.")
        return
    await message.answer("🛡 Admin Panel", reply_markup=admin_panel_kb())


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("🛡 Admin Panel", reply_markup=admin_panel_kb())


@router.callback_query(F.data == "admin_orders_list")
async def cb_admin_orders_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(Order).order_by(Order.created_at.desc()))
        orders = result.scalars().all()

    if not orders:
        await callback.message.edit_text(
            "📦 No orders found.", reply_markup=admin_panel_kb()
        )
        return

    await callback.message.edit_text(
        "📦 ORDERS\n\nSelect an order:",
        reply_markup=admin_orders_list_kb([o.order_id for o in orders]),
    )


@router.callback_query(F.data.startswith("admin_open:"))
async def cb_admin_open(callback: CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            await callback.answer("Order not found.", show_alert=True)
            return
        text = await _get_order_full(session, order)

    await callback.message.edit_text(text, reply_markup=admin_orders_kb(order_id))


@router.callback_query(F.data == "admin_search")
async def cb_admin_search(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return
    await state.set_state(AdminSearch.waiting_query)
    await callback.message.edit_text(
        "🔍 SEARCH ORDER\n\n"
        "Send an Order ID, Telegram User ID, or Username:\n\n"
        "Examples:\n"
        "ORD-20260917-0001\n"
        "or\n"
        "123456789",
        reply_markup=admin_search_kb(),
    )


@router.message(AdminSearch.waiting_query)
async def admin_search_query(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("💡 Please send a search query.", reply_markup=admin_search_kb())
        return
    keyword = query.lstrip("@").lower()

    async with async_session() as session:
        conditions = [
            Order.order_id.ilike(f"%{keyword}%"),
            Order.username.ilike(f"%{keyword}%"),
        ]
        if keyword.isdigit():
            conditions.append(Order.user_id == int(keyword))
        result = await session.execute(
            select(Order).where(or_(*conditions)).order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

    await state.clear()

    if not orders:
        await message.answer("❌ No orders found for that search.", reply_markup=admin_panel_kb())
        return

    await message.answer(
        f"🔍 Search results ({len(orders)}):",
        reply_markup=admin_orders_list_kb([o.order_id for o in orders]),
    )


@router.callback_query(F.data == "admin_search_cancel")
async def cb_admin_search_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛡 Admin Panel", reply_markup=admin_panel_kb())


@router.callback_query(F.data.startswith("admin_verify:"))
async def cb_admin_verify(callback: CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            await callback.answer("Order not found.", show_alert=True)
            return
        order.payment_status = "VERIFIED"
        order.status = "PAYMENT_VERIFICATION"
        await session.commit()
        text = await _get_order_full(session, order)
        user_id = order.user_id
        oid = order.order_id

    await callback.answer("✅ Payment verified.")
    await callback.message.edit_text(text, reply_markup=admin_orders_kb(order_id))
    await _send_user_update(
        user_id,
        f"✅ Payment Verified\n\n"
        f"Order ID:\n{oid}\n\n"
        f"Your order is now being processed.",
        bot,
    )


@router.callback_query(F.data.startswith("admin_reject:"))
async def cb_admin_reject(callback: CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            await callback.answer("Order not found.", show_alert=True)
            return
        order.payment_status = "REJECTED"
        order.status = "CANCELLED"
        await session.commit()
        text = await _get_order_full(session, order)
        user_id = order.user_id
        oid = order.order_id

    await callback.answer("❌ Payment rejected.")
    await callback.message.edit_text(text, reply_markup=admin_orders_kb(order_id))
    await _send_user_update(
        user_id,
        f"❌ Payment Rejected\n\n"
        f"Order ID:\n{oid}\n\n"
        f"Your payment was not verified. Please contact support.",
        bot,
    )


@router.callback_query(F.data.startswith("admin_processing:"))
async def cb_admin_processing(callback: CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            await callback.answer("Order not found.", show_alert=True)
            return
        order.status = "PROCESSING"
        await session.commit()
        text = await _get_order_full(session, order)
        user_id = order.user_id
        oid = order.order_id

    await callback.answer("🔄 Marked as processing.")
    await callback.message.edit_text(text, reply_markup=admin_orders_kb(order_id))
    await _send_user_update(
        user_id,
        f"🔄 Order Processing\n\n"
        f"Order ID:\n{oid}\n\n"
        f"Your order is currently being processed.",
        bot,
    )


@router.callback_query(F.data.startswith("admin_complete:"))
async def cb_admin_complete(callback: CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            await callback.answer("Order not found.", show_alert=True)
            return
        order.status = "COMPLETED"
        await session.commit()
        text = await _get_order_full(session, order)
        user_id = order.user_id
        oid = order.order_id

    await callback.answer("✅ Order completed.")
    await callback.message.edit_text(text, reply_markup=admin_orders_kb(order_id))
    await _send_user_update(
        user_id,
        f"✅ Order Completed\n\n"
        f"Order ID:\n{oid}\n\n"
        f"Your order has been completed.",
        bot,
    )


@router.callback_query(F.data.startswith("admin_cancel:"))
async def cb_admin_cancel(callback: CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Not authorized.", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            await callback.answer("Order not found.", show_alert=True)
            return
        order.status = "CANCELLED"
        await session.commit()
        text = await _get_order_full(session, order)
        user_id = order.user_id
        oid = order.order_id

    await callback.answer("❌ Order cancelled.")
    await callback.message.edit_text(text, reply_markup=admin_orders_kb(order_id))
    await _send_user_update(
        user_id,
        f"❌ Order Cancelled\n\n"
        f"Order ID:\n{oid}\n\n"
        f"Your order has been cancelled. Contact support for details.",
        bot,
    )