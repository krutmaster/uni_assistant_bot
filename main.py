import sqlite3
import telebot
from datetime import datetime
from gsheets import getShedule


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


def reg_student(id, name):

    if id != admin_id:
        base = sqlite3.connect('base.db')
        cursor = base.cursor()

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


@bot.message_handler(commands=["update_shedule"])
def setgroupadmin(message):
    id = str(message.chat.id)

    if id == admin_id:

        try:
            group_name = message.text.split()[1].upper()
            group_id = cursor.execute('select group_id from groups where name=?', (group_name,)).fetchall()[0][0]
            getShedule(group_id, group_name)
            bot.send_message(f'Расписание для групып {group_name} обновленно!')
        except Exception as e:
            bot.send_message(id, 'Такой группы не найдено или произошла ошибка')
            print(e)


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

        try:
            group_name = "".join(message.text.upper().split()[1:])
            cursor.execute("insert into groups (name) values (?)", (group_name,))
            base.commit()
            bot.send_message(id, "Группа успешно добавлена!")
        except Exception as e:
            base.rollback()
            print(e)


@bot.message_handler(content_types=['text'])
def text(message):
    id = str(message.chat.id)
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    if not cursor.execute('select group_id from students where id=?', (id,)).fetchall():
        group_name = message.text.upper()
        reg_student(id, group_name)


if __name__ == '__main__':
    bot.polling(none_stop=True)