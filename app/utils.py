from aiogram.types import Message


async def render_menu(message: Message, text: str, reply_markup=None) -> None:
    """Edit a text menu in place, or convert a media message into a fresh text menu.

    Telegrams bots cannot edit the text of a photo message (only its caption),
    so when the callback arrives on a photo/caption message we delete it and
    send a normal text message instead. This keeps every menu editable.
    """
    if getattr(message, "text", None) is not None:
        await message.edit_text(text, reply_markup=reply_markup)
    else:
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(text, reply_markup=reply_markup)