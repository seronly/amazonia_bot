from telegram import Chat
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    filters,
)
from telegram.constants import UpdateType
from sqlalchemy.exc import PendingRollbackError
import os
import dotenv
from db import Session
import custom_logging as cl
import bot
import constants

dotenv.load_dotenv()

logger = cl.logger


def main():
    application = Application.builder().token(os.getenv("API_TOKEN")).build()

    admin_ids = set(
        [int(user_id) for user_id in os.getenv("ADMIN_IDS").split(", ")]
    )
    bot.load_greeting_msg(application.bot)

    # Conversation handler
    ad_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "send_ad", bot.start_create_post, filters.User(admin_ids)
            ),
            MessageHandler(
                filters.Text(constants.SEND_AD_BTN) & filters.User(admin_ids),
                bot.start_create_post,
            ),
        ],
        states={
            constants.SEND_POST_TEXT: [
                MessageHandler(filters.Regex(
                    rf"^{constants.SKIP_BUTTON}$"), bot.skip_text),
                MessageHandler(filters.TEXT & ~ filters.COMMAND,
                               bot.get_post_text),
            ],
            constants.SEND_POST_ATTACHMENT: [
                MessageHandler(
                    filters.PHOTO
                    | filters.VIDEO,
                    bot.get_post_attachment,
                ),
                MessageHandler(filters.Regex(
                    rf"^{constants.SKIP_BUTTON}$"), bot.skip_attachment)

            ],
            constants.SEND_POST_BUTTON: [
                MessageHandler(filters.Regex(
                    rf"{constants.SKIP_BUTTON}"), bot.skip_post_button),
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               bot.get_post_button),
            ],
            constants.SEND_POST: [
                MessageHandler(filters.Regex(r"^Подтвердить$"), bot.send_ad)
            ],

        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )

    hello_msg_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "change_msg", bot.start_create_post, filters.User(admin_ids)
            ),
            MessageHandler(
                filters.Text(constants.CHANGE_MSG_BTN) & filters.User(
                    admin_ids),
                bot.start_create_post,
            ),
        ],
        states={
            constants.SEND_POST_TEXT: [
                MessageHandler(filters.Regex(
                    rf"^{constants.SKIP_BUTTON}$"), bot.skip_text),
                MessageHandler(filters.TEXT & ~ filters.COMMAND,
                               bot.get_post_text),
            ],
            constants.SEND_POST_ATTACHMENT: [
                MessageHandler(
                    filters.PHOTO
                    | filters.VIDEO,
                    bot.get_post_attachment,
                ),
                MessageHandler(filters.Regex(
                    rf"^{constants.SKIP_BUTTON}$"), bot.skip_attachment)

            ],
            constants.SEND_POST_BUTTON: [
                MessageHandler(filters.Regex(
                    rf"{constants.SKIP_BUTTON}"), bot.skip_post_button),
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               bot.get_post_button),
            ],
            constants.SEND_POST: [
                MessageHandler(filters.Regex(r"^Подтвердить$"), bot.change_msg)
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )

    application.add_handler(ad_conversation_handler)
    application.add_handler(hello_msg_conv_handler)

    # User command
    # application.add_handler(CommandHandler("start", bot.start))
    # application.add_handler(CommandHandler("help", bot.help))
    application.add_handler(ChatJoinRequestHandler(
        callback=bot.get_join_request,
        chat_id=int(os.getenv('CHANNEL_ID'))
    ))
    # Admin
    application.add_handler(
        CommandHandler(
            "admin",
            bot.admin,
            filters.User(admin_ids),
        )
    )

    application.add_handler(
        CommandHandler(
            "stats",
            bot.get_stats,
            filters.User(admin_ids),
        )
    )

    application.add_handler(
        MessageHandler(
            filters.Text(constants.CHECK_STATS_BTN) & filters.User(admin_ids),
            bot.get_stats,
        )
    )

    # Err handler
    # application.add_error_handler(bot.error_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
