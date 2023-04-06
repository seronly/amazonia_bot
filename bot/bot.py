import asyncio
from telegram import (
    Bot,
    PhotoSize,
    Video,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram._utils.types import FileInput
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from telegram.constants import ChatAction, ParseMode
from telegram.error import Forbidden
from typing import Optional, Union

from bot import db, constants
from bot import custom_logging as cl
import json
import html
import os
import re
import traceback

logger = cl.logger


class myMessage():
    msg_type: str
    text: Optional[str] = ""
    attachment: Optional[Union[FileInput, "PhotoSize", "Video", str]] = None
    kb: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None

    def __init__(
        self,
        msg_type: str = "text",
        text: Optional[str] = "",
        attachment: Optional[Union[FileInput, "PhotoSize", "Video"]] = None,
        kb: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None
    ):
        self.msg_type = msg_type
        self.text = text
        self.attachment = attachment
        self.kb = kb

    def __repr__(self) -> str:
        return f"""\
Message:
{self.msg_type=}
{self.text=}
{self.attachment=}
{self.kb=}
self
        """


greeting_message: myMessage = myMessage()
# Commands


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = constants.START_TEXT
    db.create_or_update_user(update.effective_user)
    await update.message.reply_text(text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Для того, чтобы задать вопрос, \
отправьте текст, изображение или видео"
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=constants.ADMIN_TEXT,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=constants.ADMIN_MENU_BTNS,
            resize_keyboard=True,
        ),
    )


async def start_create_post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    reply_keyboard = [[constants.SKIP_BUTTON]]
    context.user_data["post"] = myMessage()
    await context.bot.send_chat_action(
        chat_id=update.effective_user.id,
        action=ChatAction.TYPING
    )
    await update.message.reply_text(
        text="Отправьте текст или нажмите \"Пропустить\"",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True
        ),
    )
    return constants.SEND_POST_TEXT


async def get_post_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = escape_telegram_entities(update.message.text_markdown_v2_urled)
    context.user_data["post"].text = text
    await context.bot.send_chat_action(
        chat_id=update.effective_user.id,
        action=ChatAction.TYPING
    )
    await update.message.reply_text(
        "Отправьте фото или видео, или нажмите \"Пропустить\"",
    )
    return constants.SEND_POST_ATTACHMENT


async def skip_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["post"].text = ""
    await context.bot.send_chat_action(
        chat_id=update.effective_user.id,
        action=ChatAction.TYPING
    )
    await update.message.reply_text(
        "Отправьте фото или видео, или нажмите \"Пропустить\"",
    )
    return constants.SEND_POST_ATTACHMENT


async def get_post_attachment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.message.photo:
        file = update.message.photo[-1].file_id
        context.user_data["post"].attachment = file
        context.user_data["post"].msg_type = "photo"
    elif update.message.video:
        file = update.message.video.file_id
        context.user_data["post"].attachment = file
        context.user_data["post"].msg_type = "video"
    else:
        await update.message.reply_text(
            "Не потдерживаемый тип файла, "
            "отправьте другой или введите /cancel",
            reply_markup=ReplyKeyboardRemove(),
        )
        return constants.SEND_POST_ATTACHMENT

    await context.bot.send_chat_action(
        chat_id=update.effective_user.id,
        action=ChatAction.TYPING
    )

    await update.message.reply_text(
        """
Введите текст и ссылку кнопки в формате:
<code>текст кнопки - ссылка кнопки</code>
Или нажмите \"Пропустить\"
        """,
        parse_mode=ParseMode.HTML
    )
    return constants.SEND_POST_BUTTON


async def skip_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["post"].msg_type = "text"
    await update.message.reply_text(
        """
Введите текст и ссылку кнопки в формате:
<code>текст кнопки - ссылка кнопки</code>
Или нажмите \"Пропустить\"
        """,
        parse_mode=ParseMode.HTML
    )
    return constants.SEND_POST_BUTTON


async def get_post_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_btn = update.message.text.split(" - ")[0].strip()
    url_btn = update.message.text.split(" - ")[1].strip()
    context.user_data["post"].kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text=text_btn,
            url=url_btn,
        )]]
    )
    await confirm_post(update, context)
    return constants.SEND_POST


async def skip_post_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await confirm_post(update, context)
    return constants.SEND_POST


async def confirm_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post: myMessage = context.user_data["post"]
    chat_id = update.effective_user.id
    if not post.text and not post.attachment:
        await update.message.reply_text(
            "Нет сообщения и/или изображения.\nПост не был создан.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=constants.ADMIN_MENU_BTNS,
                resize_keyboard=True,
            ),
        )
        return ConversationHandler.END
    await context.bot.send_message(
        chat_id,
        text="Пост:",
        reply_markup=ReplyKeyboardMarkup(
            [[
                "Подтвердить"
            ]]
        )
    )
    await _send_message(update, context, chat_id, post)


async def send_ad(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    post: myMessage = context.user_data["post"]
    text: str | None = post.text
    users = db.get_all_users(inlcude_admin=False)
    sended_users_number = 0
    block_bot_users_number = 0

    for user in users:
        post.text = text.format(
            name=user.fullname or "Уважаемый пользователь",
            username=user.username or "",
        )
        chat_id = user.tg_id
        result = await _send_message(update, context, chat_id, post)
        if result:
            sended_users_number += 1
            if user.is_blocked:
                db.update_user(user.tg_id, {"is_blocked": False})
        else:
            db.update_user(user.tg_id, {"is_blocked": True})
            block_bot_users_number += 1
    await update.message.reply_text(
        f"Рассылка была отправлена {sended_users_number} пользователям!\n"
        f"Пользователей, заблокировавших бота \
c прошлой рассылки: {block_bot_users_number}.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=constants.ADMIN_MENU_BTNS,
            resize_keyboard=True,
        ),
    )
    return ConversationHandler.END


async def change_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post: myMessage = context.user_data["post"]
    save_greeting_msg(post)
    await context.bot.send_message(
        update.effective_user.id,
        "Изменено!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=constants.ADMIN_MENU_BTNS,
            resize_keyboard=True
        )
    )
    return ConversationHandler.END


def save_greeting_msg(msg: myMessage) -> None:
    global greeting_message
    file_path = constants.GREETING_MSG_FILE
    if msg.kb:
        msg.kb = msg.kb.to_json()

    greeting_message = msg
    with open(file_path, "w") as f:
        json.dump(msg.__dict__, f)


def load_greeting_msg(bot: Bot) -> None:
    global greeting_message
    file_path = constants.GREETING_MSG_FILE
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            greeting_message = myMessage(**json.load(f))
        if greeting_message.kb:
            greeting_message.kb = InlineKeyboardMarkup.de_json(
                json.loads(greeting_message.kb), bot)
    else:
        with open(file_path, 'w') as f:
            json.dump({}, f)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Создание рекламного поста завершено",
        reply_markup=ReplyKeyboardMarkup(constants.ADMIN_MENU_BTNS)
    )
    return ConversationHandler.END


async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_count = len(db.get_all_users(inlcude_admin=True))
    user_blocked = db.get_blocked_user_count()

    text = (
        "Статистика:\n\n"
        f"Кол-во пользователей:\n👤 {user_count}\n"
        f"Кол-во пользователей, остановиших бота:\n🚫 {user_blocked}\n"
    )
    await update.message.reply_text(text)


async def get_join_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.chat_join_request.from_user
    user_id = update.chat_join_request.api_kwargs['user_chat_id']
    db.create_or_update_user(user)

    kb = constants.FIRST_MSG_KB
    await context.bot.send_photo(
        user_id,
        photo=constants.FIRST_MSG_IMG,
        caption=constants.FIRST_MSG_TEXT,
        reply_markup=ReplyKeyboardMarkup(kb)
    )


async def send_start_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        constants.FIRST_MSG_DESC,
        reply_markup=ReplyKeyboardRemove()
    )
    await asyncio.sleep(5)
    await _send_message(update, context, user_id, greeting_message)


async def check_greeting_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await _send_message(
        update,
        context,
        update.effective_user.id,
        greeting_message
    )


async def _send_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    msg: myMessage
) -> bool:
    try:
        if msg.msg_type == "text":
            await context.bot.send_message(
                chat_id=chat_id,
                text=msg.text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=msg.kb,
            )
            return True
        file = msg.attachment
        if msg.msg_type == "photo":
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=file,
                caption=msg.text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=msg.kb,
            )
        elif msg.msg_type == "video":
            await context.bot.send_video(
                chat_id=chat_id,
                video=file,
                caption=msg.text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=msg.kb,
            )
    except Forbidden as err:
        return False
    else:
        return True


async def error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else,
    # so we can see it even if something breaks.
    logger.error(
        msg="Exception while handling an update:", exc_info=context.error
    )

    # traceback.format_exception returns the usual python message
    # about an exception,
    # but as a list of strings rather than a single string,
    # so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the message with some markup and
    # additional information about what happened.
    # You might need to add some logic to deal with messages
    # longer than the 4096 character limit.
    update_str = (
        update.to_dict() if isinstance(update, Update) else str(update)
    )
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = "
        f"{html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = "
        f"{html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = "
        f"{html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    try:
        # Finally, send the message
        await context.bot.send_message(
            chat_id=os.getenv("DEVELOPER_CHAT_ID"),
            text=message,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


def escape_telegram_entities(text):
    """
    Функция для экранирования всех зарезервированных символов в тексте.

    :param text: исходный текст
    :return: текст с экранированными символами
    """
    # Список зарезервированных символов в Telegram API
    reserved_chars = r'_*[]()~`>#+-=|{}.!'

    # Экранируем все зарезервированные символы в тексте
    return re.sub(f'([\\{reserved_chars}])', r'\\\1', text)
