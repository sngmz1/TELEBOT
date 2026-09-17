from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config import REQUIRED_CHANNEL_USERNAME, SUPPORT_USERNAME


def channel_check_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 JOIN CHANNEL", url=f"https://t.me/{REQUIRED_CHANNEL_USERNAME}")],
        [InlineKeyboardButton(text="🔄 CHECK", callback_data="check_channel")],
    ])


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Services", callback_data="services"),
         InlineKeyboardButton(text="📦 Orders", callback_data="orders")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile"),
         InlineKeyboardButton(text="➕ More", callback_data="more")],
    ])


def services_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Information Gathering", callback_data="svc:info_gathering")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="main_menu")],
    ])


def package_kb(service_key: str) -> InlineKeyboardMarkup:
    from app.services.catalog import SERVICES
    svc = SERVICES[service_key]
    buttons = []
    for pk, pkg in svc["packages"].items():
        buttons.append([InlineKeyboardButton(
            text=f"{pkg['name']} - {pkg['price']} ({pkg['max_info']} info)",
            callback_data=f"pkg:{service_key}:{pk}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="services")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def info_type_kb(service_key: str, has_items: bool, used: int, max_info: int) -> InlineKeyboardMarkup:
    from app.services.catalog import SERVICES
    svc = SERVICES[service_key]
    buttons = []
    for t in svc["info_types"]:
        buttons.append([InlineKeyboardButton(text=f"📌 {t['type']}", callback_data=f"info_type:{t['key']}")])
    if has_items and used < max_info:
        buttons.append([InlineKeyboardButton(text="✅ DONE & CONTINUE", callback_data="info_done")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data=f"svc:{service_key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def info_action_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ ADD ANOTHER", callback_data="info_addmore")],
        [InlineKeyboardButton(text="✅ DONE & CONTINUE", callback_data="info_done")],
    ])


def order_confirm_kb(service_key: str, package_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ CONFIRM", callback_data=f"confirm:{service_key}:{package_key}")],
        [InlineKeyboardButton(text="❌ CANCEL", callback_data="services")],
    ])


def support_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 CONTACT SUPPORT", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton(text="◀️ Main Menu", callback_data="main_menu")],
    ])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Main Menu", callback_data="main_menu")],
    ])


def order_history_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 ORDER HISTORY", callback_data="order_history")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="main_menu")],
    ])


def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 ORDER HISTORY", callback_data="order_history")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="main_menu")],
    ])


def more_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton(text="📜 Terms & Conditions", callback_data="tnc")],
        [InlineKeyboardButton(text="🔐 Privacy Policy", callback_data="privacy")],
        [InlineKeyboardButton(text="ℹ️ About", callback_data="about")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="main_menu")],
    ])


def admin_orders_kb(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ VERIFY PAYMENT", callback_data=f"admin_verify:{order_id}")],
        [InlineKeyboardButton(text="❌ REJECT PAYMENT", callback_data=f"admin_reject:{order_id}")],
        [InlineKeyboardButton(text="🔄 PROCESSING", callback_data=f"admin_processing:{order_id}")],
        [InlineKeyboardButton(text="✅ COMPLETE", callback_data=f"admin_complete:{order_id}")],
        [InlineKeyboardButton(text="❌ CANCEL", callback_data=f"admin_cancel:{order_id}")],
        [InlineKeyboardButton(text="🔙 BACK", callback_data="admin_orders_list")],
    ])


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 ORDERS", callback_data="admin_orders_list")],
        [InlineKeyboardButton(text="🔍 SEARCH ORDER", callback_data="admin_search")],
    ])


def admin_orders_list_kb(order_ids: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for oid in order_ids:
        buttons.append([InlineKeyboardButton(text=f"📦 {oid}", callback_data=f"admin_open:{oid}")])
    buttons.append([InlineKeyboardButton(text="🔍 SEARCH", callback_data="admin_search")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_search_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin_panel")],
    ])


def admin_notification_kb(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 OPEN ORDER", callback_data=f"admin_open:{order_id}")],
    ])