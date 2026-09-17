from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func as sql_func
from app.database.db import async_session, User, Order, OrderInformation
from app.keyboards.buttons import profile_kb, back_to_menu_kb
from app.utils import render_menu

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


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    uid = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == uid))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=uid,
                username=callback.from_user.username or "",
                full_name=callback.from_user.full_name,
            )
            session.add(user)
            await session.commit()
        else:
            user.username = callback.from_user.username or user.username
            user.full_name = callback.from_user.full_name
            await session.commit()

        total = await session.execute(select(sql_func.count(Order.id)).where(Order.user_id == uid))
        total_orders = total.scalar() or 0

        completed = await session.execute(select(sql_func.count(Order.id)).where(Order.user_id == uid, Order.status == "COMPLETED"))
        completed_orders = completed.scalar() or 0

        pending = await session.execute(select(sql_func.count(Order.id)).where(Order.user_id == uid, Order.status.in_(["PENDING_PAYMENT", "PAYMENT_VERIFICATION", "PROCESSING"])))
        pending_orders = pending.scalar() or 0

    text = (
        f"👤 PROFILE\n\n"
        f"Name:\n{callback.from_user.full_name}\n"
        f"Username:\n@{callback.from_user.username or 'N/A'}\n"
        f"Telegram ID:\n{uid}\n\n"
        f"Total Orders: {total_orders}\n"
        f"Completed: {completed_orders}\n"
        f"Pending: {pending_orders}"
    )

    await render_menu(callback.message, text, profile_kb())


@router.callback_query(F.data == "order_history")
async def cb_order_history(callback: CallbackQuery):
    uid = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.user_id == uid).order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

    if not orders:
        await render_menu(
            callback.message,
            "📦 No orders yet.",
            back_to_menu_kb(),
        )
        return

    lines = ["📦 ORDER HISTORY\n"]
    for o in orders:
        status_label = ORDER_STATUS_LABELS.get(o.status, o.status)
        info_count = await _order_info_count(o.order_id)
        order_word = "Order" if info_count == 1 else "Orders"
        lines.append(
            f"📦 {o.order_id}\n"
            f"{o.service}\n"
            f"{o.package}\n"
            f"{info_count} {order_word}\n"
            f"💰 {o.amount}\n\n"
            f"Status: {status_label}\n"
            f"📅 {o.created_at.strftime('%d %b %Y')}\n"
            f"---"
        )

    await render_menu(callback.message, "\n".join(lines), back_to_menu_kb())


async def _order_info_count(order_id: str) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(sql_func.count(OrderInformation.id)).where(OrderInformation.order_id == order_id)
        )
        return result.scalar() or 0