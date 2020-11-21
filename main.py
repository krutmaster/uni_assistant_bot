import sqlite3
import telebot
from keyboa import keyboa_maker, keyboa_combiner
from datetime import datetime, date, timedelta
from gsheets import getShedule, createSheet
from time import sleep
from threading import Thread
import calendar


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
                menu(id=id)
            else:
                bot.send_message(id, 'Я не нашёл такую группу. Проверь, правильно ли ты написал')

        except Exception as e:
            ErrorLog(e)


def evenWeek():
    if int(date.today().strftime("%j")) > int(date(2020, 9, 1).strftime("%j")):
        return (abs(int(date.today().strftime("%j")) - int(date(2020, 9, 1).strftime("%j"))) // 7 + 1) % 2
    else:
        return (abs(365 + int(date.today().strftime("%j")) - int(date(2020, 9, 1).strftime("%j"))) // 7 + 1) % 2


def send_notifications(notif_deadline):
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    try:
        smile_fire = u'\U0001F525'
        date = datetime.now().date()
        deadline = str(date + timedelta(days=notif_deadline))
        tasks = cursor.execute('select task_id from tasks where deadline=?', (deadline,)).fetchall()

        for task in tasks:
            task = task[0]
            groups = cursor.execute('select group_id from task_group where task_id=?', (task,)).fetchall()

            for group in groups:
                group = group[0]
                students = cursor.execute('select id from students where group_id=? and notif_deadline=?', (group, notif_deadline,)).fetchall()

                for student in students:
                    student = student[0]
                    task_name = cursor.execute('select task from tasks where task_id=?', (task,)).fetchall()[0][0]
                    bot.send_message(student, f'{smile_fire}{smile_fire}{smile_fire} ВНИМАНИЕ!!! {smile_fire}{smile_fire}{smile_fire}\n\n'
                                     f'Крайний срок сдачи задания "{task_name}" {deadline}.\nЕсли захочешь изменить настройки напоминания, открой их '
                                     f'в /menu')

    except Exception as e:
        ErrorLog(e)


def del_task():
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    date = datetime.now().date()

    try:
        tasks = cursor.execute('delete tasks where deadline=?', (date,))
        base.commit()
    except Exception as e:
        base.rollback()
        ErrorLog(e)



def synchronization():

    try:

        while True:
            hours = datetime.now().hour

            if hours == 20:
                del_task()

                for i in range(7):
                    send_notifications(7 - i)

                sleep(86400)

            elif hours > 10:
                minutes = datetime.now().minute
                sleep((24 - hours + 9) * 3600 + (60 - minutes) * 60)
            else:
                minutes = datetime.now().minute
                sleep((9 - hours) * 3600 + (60 - minutes) * 60)

    except Exception as e:
        ErrorLog(e)


def set_notif_deadline(id):
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    try:
        notif_deadline = cursor.execute('select notif_deadline from students where id=?', (id,)).fetchall()
        buttons = [
            {'1': 'set_notif_deadline 1'},
            {'2': 'set_notif_deadline 2'},
            {'3': 'set_notif_deadline 3'},
            {'4': 'set_notif_deadline 4'},
            {'5': 'set_notif_deadline 5'},
            {'6': 'set_notif_deadline 6'},
            {'7': 'set_notif_deadline 7'}
        ]
        kb_menu = keyboa_maker(items=buttons)

        if notif_deadline is not None:
            bot.send_message(id, f'Бот напомнит о сроках сдачи задания за {notif_deadline[0][0]} '
                                 f'дней до крайнего срока.\nЕсли хотите изменить, то выберите новое значение',
                             reply_markup=kb_menu)
        else:
            bot.send_message(id, 'Выберите, за сколько дней боту напоминать о приближении срока сдачи задания',
                             reply_markup=kb_menu)
    except Exception as e:
        ErrorLog(e)


@bot.message_handler(commands=["menu"])
def menu(message=None, id=None):

    if not id:
        id = str(message.chat.id)

    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    try:
        buttons = [
            {"Мое расписание": "schedule"},
            {"Настройки уведомлений о дедлайнах": "notif_set"},
            {"Календарь дедлайнов": "deadlines"}]
        kb_menu = keyboa_maker(items=buttons)
        group_id = cursor.execute("select group_id from students where id=?", (id,)).fetchall()[0][0]
        group_name = cursor.execute("select name from groups where id=?", (group_id,)).fetchall()[0][0]
        bot.send_message(id, f"Ты принадлежишь к группе {group_name}\nВыбери один из пунктов меню",
                         reply_markup=kb_menu)
    except Exception as e:
        ErrorLog(e)


@bot.message_handler(commands=["update_shedule"])
def update_shedule(message):
    id = str(message.chat.id)
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    if id == admin_id:

        try:
            group_name = message.text.split()[1].upper()
            group_id = cursor.execute('select id from groups where name=?', (group_name,)).fetchall()[0][0]
            bot.send_message(id, 'Ожидайте, расписание обновляется')
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
            createSheet(group_name)
            bot.send_message(id, 'Группа успешно добавлена!\nСоздана страница в таблице бота, '
                                 'используйте её для редактирования расписания группы. После '
                                 'заполнения расписания используйте команду "/update_shedule ГРУППА1"')
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
        task_text = " ".join(message.text.split()[1:])
        cursor.execute("insert into tasks (task) values (?)", (task_text,))
        base.commit()
        task_id = cursor.execute("select max(task_id) from tasks").fetchall()[0][0]
        bot.send_message(id, f"Вы добавляете новое задание: \"{task_text}\"\nТеперь перечислите группы, которым "
                             f"необходимо выполнить задание, в формате \n\"{task_id} ГРУППА1, ГРУППА2,...\"")


def shedule(id):
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    weekday = datetime.today().isoweekday()
    isEven = evenWeek()

    try:

        if weekday == 7:
            bot.send_message(id, "Сегодня воскресенье, не парься, просто отдыхай :)")
        else:
            group_id = cursor.execute("select group_id from students where id=?", (id,)).fetchall()[0][0]
            lessons = cursor.execute("select name from shedule where week_day=? and is_even=? and group_id=?",
                                     (weekday, isEven, group_id,)).fetchall()
            schedule = ""

            for i, lesson in enumerate(lessons):

                if lesson[0] != "" and lesson[0] != 'NULL':
                    link = cursor.execute("select link from shedule where week_day=? and is_even=? and group_id=?",
                                     (weekday, isEven, group_id,)).fetchall()[0][0]
                    schedule += f"{i + 1} пара: {lesson[0]}\nСсылка на конференцию: {link}\n\n"

            bot.send_message(id, "Твое расписание на сегодня:\n" + schedule)

        menu(id=id)
    except Exception as e:
        ErrorLog(e)


def deadline_calendar(id):
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    smile_skull = u'\U0001F480'
    year = date.today().strftime("%Y")
    month = date.today().strftime("%m")
    day_count = calendar.Calendar().monthdays2calendar(int(year), int(month))
    group_id = cursor.execute("select group_id from students where id=?", (id,)).fetchall()[0][0]
    tasks_id = cursor.execute("select task_id from task_group where group_id=?", (group_id,)).fetchall()
    dd_dates = []
    for i in tasks_id:
        db_date = cursor.execute("select deadline from tasks where task_id=?", (i[0],)).fetchall()[0][0]
        if db_date[5:] not in dd_dates:
            dd_dates.append(db_date[5:])
    buttons = []
    for i in range(len(day_count)):
        buttons.append([])
        for j in range(len(day_count[i])):
            if day_count[i][j][0] == 0:
                buttons[i].append({" ": "EmptyBtn"})
            else:
                tempdate = f"{month}-{day_count[i][j][0]}"
                if tempdate in dd_dates:
                    if len(str(day_count[i][j][0])) == 1:
                        buttons[i].append({str(day_count[i][j][0]) + smile_skull: f"DeadBtn0{day_count[i][j][0]}"})
                    else:
                        buttons[i].append({str(day_count[i][j][0]) + smile_skull: f"DeadBtn{day_count[i][j][0]}"})
                else:
                    buttons[i].append({str(day_count[i][j][0]): f"CalBtn{day_count[i][j][0]}"})
    menu_button = [{"Вернуться в меню": "menu"}]
    kb_calendar = keyboa_maker(items=buttons)
    kb_menu = keyboa_maker(items=menu_button)
    kb = keyboa_combiner(keyboards=(kb_calendar, kb_menu))
    bot.send_message(chat_id=id, text="Календарь дедлайнов", reply_markup=kb)






@bot.callback_query_handler(func=lambda x: True)
def buttons(call):
    id = str(call.from_user.id)
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    if call.data == "schedule":
        shedule(id)
    elif call.data == "changeTrue":

        try:
            cursor.execute("delete from students where id=?", (id,))
            base.commit()
            bot.send_message(id, "Я удалил тебя из базы данных. Теперь еще раз напиши свою группу, чтобы я смог тебя зарегистрировать")
        except Exception as e:
            base.rollback()
            ErrorLog(e)

    elif call.data == "changeFalse":
        menu(id=id)
    elif call.data == 'notif_set':
        set_notif_deadline(id)
    elif call.data.split()[0] == 'set_notif_deadline':

        try:
            notif_deadline = int(call.data.split()[1])
            cursor.execute('update students set notif_deadline=? where id=?', (notif_deadline, id,))
            base.commit()
            bot.send_message(id, 'Время напоминания успешно сохранено!')
        except Exception as e:
            base.rollback()
            ErrorLog(e)
    elif call.data == "deadlines":
        deadline_calendar(id)
    elif call.data.startswith("CalBtn"):
        bot.send_message(id, "На этот день нет никаких задач.")
        deadline_calendar(id)
    elif call.data.startswith("DeadBtn"):
        stud_info = cursor.execute("select group_id from students where id=?", (id,)).fetchall()[0][0]
        task_id = cursor.execute("select task_id from task_group where group_id=?", (stud_info,)).fetchall()
        task_id = [task_id[x][0] for x in range(len(task_id))]
        deadline_date = f'{datetime.today().strftime("%Y-%m")}-{call.data[7:]}'
        tasks = []
        for i in task_id:
            task = cursor.execute("select task from tasks where task_id=? and deadline=?", (str(i), deadline_date,)).fetchall()[0][0]
            tasks.append(task)
        tasks = '\n'.join(tasks)
        bot.send_message(id, f"Ваши задачи на {call.data[7:]}.{datetime.today().strftime('%m.%Y')}:\n{tasks}")
        deadline_calendar(id)
    elif call.data == "menu":
        menu(id=id)


@bot.message_handler(content_types=['text'])
def text(message):
    id = str(message.chat.id)
    base = sqlite3.connect('base.db')
    cursor = base.cursor()

    if id == admin_id:
        task_id = message.text.split()[0]

        if not cursor.execute("select task_id from task_group where task_id=?", (task_id,)).fetchall():
            groups = "".join(message.text.upper().split()[1:]).split(",")
            added_groups = []

            try:

                for group in groups:
                        group_id = cursor.execute("select id from groups where name=?", (group,)).fetchall()

                        if group_id:
                            group_id = group_id[0][0]
                            cursor.execute("insert into task_group values (?, ?)", (task_id, group_id,))
                            added_groups.append(group)
                        else:
                            bot.send_message(id, f'Группа {group} не найдена среди добавленных и пропущена для'
                                                 f' задания')

                base.commit()
                bot.send_message(id, "К заданию были добавлены группы:\n{}\nТеперь введите крайний срок сдачи задания"
                                     " в фомате\n\"{} ГГГГ-ММ-ДД\"".format("\n".join(added_groups), task_id))
            except Exception as e:
                base.rollback()
                ErrorLog(e)

        else:

            try:
                task_id = message.text.split()[0]
                deadline = message.text.split()[1]
                cursor.execute("update tasks set deadline=? where task_id=?", (deadline, task_id,))
                base.commit()
                bot.send_message(id, "Задача успешно добавлена!")
            except Exception as e:
                base.rollback()
                ErrorLog(e)

    elif not cursor.execute('select group_id from students where id=?', (id,)).fetchall():
        group_name = message.text.upper()
        reg_student(id, group_name)


if __name__ == '__main__':
    synchronization_thread = Thread(target=synchronization)
    synchronization_thread.start()
    bot.polling(none_stop=True)
