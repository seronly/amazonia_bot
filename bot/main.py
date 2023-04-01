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

    # Conversation handler
    ad_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "send_ad", bot.start_send_ad, filters.User(admin_ids)
            ),
            MessageHandler(
                filters.Text(constants.SEND_AD_BTN) & filters.User(admin_ids),
                bot.start_send_ad,
            ),
        ],
        states={
            constants.SEND_AD_TEXT: [
                MessageHandler(filters.TEXT, bot.send_ad_text)
            ],
            constants.SEND_AD_ATTACHMENT: [
                MessageHandler(
                    filters.PHOTO
                    | filters.VIDEO
                    | filters.Regex(r"^(Да|Нет)$"),
                    bot.send_ad_attachment,
                )
            ],
            constants.SEND_AD_BUTTON: [
                MessageHandler(filters.TEXT, bot.send_ad_button)
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )

    application.add_handler(ad_conversation_handler)

    # User command
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help))
    application.add_handler(ChatJoinRequestHandler(
        callback=bot.get_join_request,
        # chat_id=os.getenv('CHANNEL_ID')
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
