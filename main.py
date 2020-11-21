import sqlite3
import telebot
from keyboa import keyboa_maker
from datetime import datetime, date
from gsheets import getShedule


base = sqlite3.connect('base.db')
cursor = base.cursor()
token = cursor.execute('select token from Settings').fetchall()[0][0]
admin_id = cursor.execute('select admin_id from Settings').fetchall()
if admin_id:
    admin_id = admin_id[0][0]
bot = telebot.TeleBot(token)


def ErrorLog(exc):
    print(exc)
    '''
    with open('log.txt', 'w') as log_file:
        log_file.write(f'<Error {datetime.now()}\nreg_student\n{id}\n{e}\n/>')
    '''


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
                menu(id)
            else:
                bot.send_message(id, 'Я не нашёл такую группу. Проверь, правильно ли ты написал')
        except Exception as e:
            ErrorLog(e)


def evenWeek():
    if int(date.today().strftime("%j")) > int(date(2020, 9, 1).strftime("%j")):
        return (abs(int(date.today().strftime("%j")) - int(date(2020, 9, 1).strftime("%j"))) // 7 + 1) % 2
    else:
        return (abs(365 + int(date.today().strftime("%j")) - int(date(2020, 9, 1).strftime("%j"))) // 7 + 1) % 2


def menu(id):
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    try:
        buttons = [
            [{"Мое расписание": "schedule"},
            {"Мои задачи": "tasks"}],
            {"Настройки уведомлений о дедлайнах": "notif_set"},
            {"Календарь дедлайнов": "deadlines"}]
        kb_menu = keyboa_maker(items=buttons)
        group_id = cursor.execute("select group_id from students where id=?", (id,)).fetchall()[0][0]
        group_name = cursor.execute("select name from groups where id=?", (group_id,)).fetchall()[0][0]
        bot.send_message(chat_id=id, reply_markup=kb_menu, text=f"Ты принадлежишь к группе {group_name}\nВыбери один из пунктов меню")
    except Exception as e:
        ErrorLog(e)


@bot.message_handler(commands=["update_shedule"])
def update_shedule(message):
    id = str(message.chat.id)

    if id == admin_id:

        try:
            group_name = message.text.split()[1].upper()
            group_id = cursor.execute('select group_id from groups where name=?', (group_name,)).fetchall()[0][0]
            getShedule(group_id, group_name)
            bot.send_message(f'Расписание для группы {group_name} обновленно!')
        except Exception as e:
            bot.send_message(id, 'Такой группы не найдено или произошла ошибка')
            ErrorLog(e)


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
            ErrorLog(e)


@bot.message_handler(commands=["change_group"])
def change_group(message):
    global admin_id
    id = str(message.chat.id)

    if id != admin_id:
        buttons = [[{"Да": "changeTrue"}, {"Нет": "changeFalse"}]]
        kb_menu = keyboa_maker(items=buttons)
        bot.send_message(chat_id=id, reply_markup=kb_menu, text="Ты уверен, что хочешь изменить группу?")


@bot.message_handler(commands=["add_task"])
def add_task(message):
    global admin_id
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    id = str(message.chat.id)
    if id == admin_id:
        task_text = " ".join(message.text().split()[1:])
        cursor.execute("insert into tasks task values ?", (task_text,))
        base.commit()
        task_id = cursor.execute("select task_id from tasks where task=?", (task_text,)).fetchall()[0][0]
        bot.send_message(f"Вы добавляете новое задание: \"{task_text}\"\nТеперь перечислите группы, которым необходимо выполнить задание в формате \n\"{task_id} группа 1, группа 2,...\"")


@bot.callback_query_handler(func=lambda x: True)
def buttons(call):
    id = str(call.from_user.id)
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    if call.data == "schedule":
        weekday = datetime.today().isoweekday()
        isEven = evenWeek()

        try:

            if weekday == 7:
                bot.send_message(id, "Сегодня воскресенье, не парься, просто отдыхай :)")
            else:
                group_id = cursor.execute("select group_id from students where id=?", (id,)).fetchall()[0][0]
                lessons = cursor.execute("select name from shedule where week_day=? and is_even=? and group_id=?", (weekday, isEven, group_id,)).fetchall()
                schedule = ""

                for i, lesson in enumerate(lessons):

                    if lesson[0] != "":
                        schedule += f"{i + 1} пара: {lesson[0]}\n"

                bot.send_message(id, "Твое расписание на сегодня:\n" + schedule)
                menu(id)
        except Exception as e:
            ErrorLog(e)

    if call.data == "changeTrue":

        try:
            cursor.execute("delete from students where id=?", (id,))
            base.commit()
            bot.send_message(id, "Я удалил тебя из базы данных. Теперь еще раз напиши свою группу, чтобы я смог тебя зарегистрировать")
        except Exception as e:
            base.rollback()
            ErrorLog(e)

    elif call.data == "changeFalse":
        menu(id)


@bot.message_handler(content_types=['text'])
def text(message):
    id = str(message.chat.id)
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    if not cursor.execute('select group_id from students where id=?', (id,)).fetchall():
        group_name = message.text.upper()
        reg_student(id, group_name)
    elif not cursor.execute("select task_id from task_group where task_id=?", (message.text()[0],)).fetchall():
        task_id = message.text()[0]
        groups = message.text()[2:].upper().split(",")
        added_groups = []
        for i in range(len(groups)):
            groups[i] = "".join(groups[i].split())
        for i in range(len(groups)):
            try:
                if cursor.execute("select id from groups where name=?", (groups[i],)).fetchall():
                    group_id = cursor.execute("select id from groups where name=?", (groups[i],))[0][0]
                    cursor.execute("insert into task_group values (?, ?)", (task_id, group_id,))
                    base.commit()
                    added_groups.append(groups[i])
            except Exception as e:
                base.rollback()
                ErrorLog(e)
        bot.send_message("К заданию были добавлены группы: {}\nТеперь введите крайний срок сдачи задания в фомате \"{} ГГГГ-ММ-ДД\"".format("\n".join(added_groups), task_id))
    elif not cursor.execute("select deadline from tasks where task_id=?", (message.text()[0],)).fetchall():
        try:
            cursor.execute("update tasks set deadline=?", (message.text())[1:])
            base.commit()
        except Exception as e:
            base.rollback()
            ErrorLog(e)




if __name__ == '__main__':
    bot.polling(none_stop=True)