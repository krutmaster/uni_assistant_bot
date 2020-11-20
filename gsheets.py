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


def getShedule(group_id):
    base = sqlite3.connect('base.db')
    cursor = base.cursor()
    name_group = cursor.execute('select name from groups where id=?', (group_id,)).fetchall()[0][0]
    wks = sh.worksheet_by_title(f'shedule_{name_group}')

    if cursor.execute('select lesson from shedule where group_id=?', (group_id,)).fetchall():
        cursor.execute('delete from shedule where group_id=?', (group_id,))
    '''
    cells = wks.get_col(2, returnas='cell')
            edge = 'B'

        for cell in cells:
            order_ = cell.value

            if order_ == str(order):
                return str(cell.address).split(edge)[1].split('>')[0]
    '''
    for i in range(6):
        col = i + 2
        cells = wks.get_col(col, returnas='cell')[1:]
        week_day = i + 1

        for j, cell in enumerate(cells):

            if j % 2 == 0:
                row = int(str(cell.address).split(col_chars[i])[1].split('>')[0])

                if j == 2 or j == 4:
                    lesson = 1

                    if j == 2:
                        is_even = 0
                    else:
                        is_even = 1

                elif j == 6 or j == 8:
                    lesson = 2

                    if j == 6:
                        is_even = 0
                    else:
                        is_even = 1

                elif j == 10 or j == 12:
                    lesson = 3

                    if j == 10:
                        is_even = 0
                    else:
                        is_even = 1

                elif j == 14 or j == 16:
                    lesson = 4

                    if j == 14:
                        is_even = 0
                    else:
                        is_even = 1

                else:
                    lesson = 5

                    if j == 18:
                        is_even = 0
                    else:
                        is_even = 1

                name = cell.value
            else:
                link = cell.value
                cursor.execute('insert into shedule values (?, ?, ?, ?, ?, ?)',
                               (lesson, week_day, name, link, is_even, group_id,))

    base.commit()
