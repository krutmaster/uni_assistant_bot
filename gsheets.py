import pygsheets
import sqlite3


gc = pygsheets.authorize()
sh = gc.open('Uni_assistent_bot')
col_chars = {
    0: 'B',
    1: 'C',
    2: 'D',
    3: 'E',
    4: 'F',
    5: 'G'
}
name_col = {
    2: '1 нечётная',
    4: '1 чётная',
    6: '2 нечётная',
    8: '2 чётная',
    10: '3 нечётная',
    12: '3 чётная',
    14: '4 нечётная',
    16: '4 чётная',
    18: '5 нечётная',
    20: '5 чётная'
}


def getShedule(group_id, name_group):
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    wks = sh.worksheet_by_title(f'shedule_{name_group}')

    if cursor.execute('select lesson from shedule where group_id=?', (group_id,)).fetchall():
        cursor.execute('delete from shedule where group_id=?', (group_id,))

    for i in range(6):
        col = i + 2
        cells = wks.get_col(col, returnas='cell')[1:]
        week_day = i + 1

        for j, cell in enumerate(cells):

            if j % 2 == 0:
                #row = int(str(cell.address).split(col_chars[i])[1].split('>')[0])

                if j == 0 or j == 2:
                    lesson = 1

                    if j == 0:
                        is_even = 1
                    else:
                        is_even = 0

                elif j == 4 or j == 6:
                    lesson = 2

                    if j == 4:
                        is_even = 1
                    else:
                        is_even = 0

                elif j == 8 or j == 10:
                    lesson = 3

                    if j == 8:
                        is_even = 1
                    else:
                        is_even = 0

                elif j == 12 or j == 14:
                    lesson = 4

                    if j == 12:
                        is_even = 1
                    else:
                        is_even = 0

                else:
                    lesson = 5

                    if j == 16:
                        is_even = 1
                    else:
                        is_even = 0

                name = cell.value
            else:
                link = cell.value
                cursor.execute('insert into shedule values (?, ?, ?, ?, ?, ?)',
                               (lesson, week_day, name, link, is_even, group_id,))

    base.commit()


def createSheet(group_name):
    wks = sh.add_worksheet(f'shedule_{group_name}', rows=21, cols=7)
    wks.update_values('A1:G1', [['Пара', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']])

    for row in range(2, 22):

        if row % 2 == 0:
            wks.update_value(f'A{row}', name_col[row])
        else:
            wks.update_value(f'A{row}', 'Ссылка на пару')
