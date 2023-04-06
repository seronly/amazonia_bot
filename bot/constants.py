# Texts
START_TEXT = "Добро пожаловать!\n\
Для того, чтобы задать вопрос, отправьте текст или изображение."
ADMIN_TEXT = """/send_ad - Отправить рассылку
/change_msg - Изменить приветственное сообщение
/check_msg - Проверить приветственное сообщение
/stats - получить статистику бота"""

# Buttons
TYPE_IMG_TEXT = "Картинка"
TYPE_TXT_TEXT = "Текст"
SEND_AD_BTN = "Отправить рассылку"
CHANGE_MSG_BTN = "Изменить приветственное сообщение"
CHECK_STATS_BTN = "Посмотреть статистику"
CHECK_GREETING_MSG = "Посмотреть приветственное сообщение"
SKIP_BUTTON = "Пропустить"
ADMIN_MENU_BTNS = [[SEND_AD_BTN, CHANGE_MSG_BTN],
                   [CHECK_STATS_BTN, CHECK_GREETING_MSG]]
# ConversationHandler
SEND_POST_TEXT, SEND_POST_ATTACHMENT, SEND_POST_BUTTON, SEND_POST = range(
    4)

# Join request message
FIRST_MSG_TEXT = "⁉️ЧТО ЭТО ЗА СУЩЕСТВО⁉️"
FIRST_MSG_IMG = './first_msg.jpg'
FIRST_MSG_KB = [["Долгопят"], ["Лемур Коми"], ["Обезьяна"]]

# Files
GREETING_MSG_FILE = './hello_msg.json'
