import sqlite3
import telebot


base = sqlite3.connect('base.db')
cursor = base.cursor()
token = cursor.execute('select token from Settings').fetchall()[0][0]
admin_id = cursor.execute('select admin_id from Settings').fetchall()
if admin_id:
    admin_id = admin_id[0][0]
bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start"])
def start(message):
    id = str(message.chat.id)

    if id != admin_id:
        bot.reply_to(message, 'Привет! Этот бот призван упростить')


@bot.message_handler(commands=["setgroupadmin"])
def setgroupadmin(message):
    global admin_id
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    id = str(message.chat.id)

    try:

        if not admin_id:
            admin_id = id
            cursor.execute('update Settings set admin_id=?', (admin_id,))
            base.commit()
            bot.send_message(id, 'Данная группа установлена по умолчанию для админов.')
    except:
        base.rollback()
        bot.send_message(id, 'Команда введена неправильно, попробуйте ещё раз.')
