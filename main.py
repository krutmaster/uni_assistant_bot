import sqlite3
import telebot
from datetime import datetime


base = sqlite3.connect('base.db')
cursor = base.cursor()
token = cursor.execute('select token from Settings').fetchall()[0][0]
admin_id = cursor.execute('select admin_id from Settings').fetchall()
if admin_id:
    admin_id = admin_id[0][0]
bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start"])
def start(message):
    global status_reg
    id = str(message.chat.id)

    if id != admin_id:
        bot.send_message(id, 'Привет! Я бот-ассистент для студентов вузов, призванный для упрощения'
        ' учебного процесса. Прежде чем начать, давай познакомимся. Напиши свою группу')


@bot.message_handler(content_types=['text'])
def text(message):
    id = str(message.chat.id)
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    if not cursor.execute('select group_id from students where id=?', (id,)).fetchall():
        group_name = message.text.upper()
        reg_student(id, group_name)


def reg_student(id, name):
    global admin_id
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    if id != admin_id:
        try:
            group_id = cursor.execute('select id from groups where name=?', (name,)).fetchall()

            if group_id:
                group_id = group_id[0][0]
                cursor.execute('insert into students values (?, ?, Null)', (id, group_id,))
                base.commit()
                bot.send_message(id, 'Регистрация прошла успешно')
            else:
                bot.send_message(id, 'Я не нашёл такую группу. Проверь, правильно ли ты написал')
        except Exception as e:
            print(e)
            '''
            with open('log.txt', 'w') as log_file:
                log_file.write(f'<Error {datetime.now()}\nreg_student\n{id}\n{e}\n/>')
            '''


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


@bot.message_handler(commands=["add_group"])
def add_group(message):
    global admin_id
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    id = str(message.chat.id)
    if id == admin_id:
        group_name = "".join(message.text.upper().split()[1:])
        cursor.execute("insert into groups values name=?", (group_name,))
        bot.send_message("Группа успешно добавлена!")
        base.commit()




if __name__ == '__main__':
    bot.polling(none_stop=True)
