# TELEGRAM-БОТ

# Импорт библиотек
import sqlite3 as sl;
import telebot, telebot.types as types;
from docxtpl import DocxTemplate;
from io import BytesIO;
from datetime import datetime as dt;

# ТЕКСТОВЫЕ ШАБЛОНЫ
building_text = r'''f"""
🏣 Информация о здании:

🆔 Кадастровый номер: {x[0]}
🗺 Адрес: {x[1]}
🏙 Район: {x[2]}
🚩 Площадь земного участка: {x[3]} м²
🏗 Год постройки: {x[4]}
🧱 Материал: {x[5]}
🔲 Материал фундамента: {x[6]}
➖ Износ в процентах: {x[8]}%
🛣 Расстояние от центра города: {x[10]} м
⭐️ Площадь нежилого помещения: {x[11]} м²
🔼 Количество этажей: {x[9]}
🚪 Количество квартир: {x[13]}
↕️ Лифт: p

🗒 Примечание:
{x[7]}
"""''';

new_flat = '''
Введите следующие данные для добавления квартиры:
1. Номер этажа
2. Номер квартиры
3. Количество комнат
4. Жилая площадь квартиры
5. Вспомогательная площадь квартиры
6. Площадь балкона
7. Высота квартиры
'''

new_building = '''
Введите следующие данные для добавления здания:
1. Кадастровый номер
2. Адрес
3. Район города
4. Площадь земельного участка
5. Год постройки здания
6. Материал стен здания
7. Материал фундамента
8. Износ в процентах
9. Число этажей в здании
10. Расстояние от центра города
11. Площадь нежилых помещений
12. Количество квартир в здании
13. Наличие лифта
'''

flatsql = '''
SELECT BUILDINGS.Kadastr, BUILDINGS.Address, Storey, Flat, Rooms, Squareflat, Dwell, Branch, Balcony, Height, Fid
FROM FLATS, BUILDINGS WHERE Flat = ? AND Fid IN (SELECT Fid FROM RECORDS WHERE Kadastr IN (SELECT Kadastr FROM USERS WHERE Id = ?))
''';

flat_text = r'''f"""
🏣 Информация о здании:

🆔 Кадастровый номер: {x[0]}
🗺 Адрес: {x[1]}
🔼 Этаж: {x[2]}
🚪 Номер квартиры: {x[3]}
🛌 Число комнат: {x[4]}
🔲 Площадь квартиры: {x[5]} м²
❤️ Жилая площадь: {x[6]} м²
⭐️ Вспомогательная площадь: {x[7]} м²
🪟 Площадь балкона: {x[8]} м²
✈️ Высота потолка: {x[9]} м
"""''';

def get_button(x):
    return types.ReplyKeyboardMarkup(row_width = x, resize_keyboard = True);

# Функция для смены шага
def next_step(user_id, step):
    db.execute('UPDATE USERS SET Step = ? WHERE Id = ?', (step, user_id, ));
    db.commit();

db = sl.connect('database_pr.db', check_same_thread = False);
bot = telebot.TeleBot('5364881295:AAF9JCR0Ci3FoIVEnDFzatqebNE83xWVPvE');

# КНОПКИ TELEGRAM
# Главное меню
mainmenu = get_button(2).add('🔍 Поиск', '➕ Новое здание'); # 🏡 Жилые здания

# Когда здание найдено
buildingmenu = get_button(2).add('🏠 Поиск квартиры',
    '➕ Новая квартира', '📝 Редактировать', '🚪 Выход'); # 🔍 Поиск
editbuildingmenu = get_button(3).add('🖼 Картинка', '🗒 Примечание', '🚪 Выход'); # 📝 Редактировать информацию

# Когда квартира уже найдена
flatmenu = get_button(2).add('👨‍💼 Владельцы', '🚪 Выход'); # 🏠 Поиск квартиры

# Изменить владельцев
editownersmenu = get_button(3).add('👨‍💼 Новый владелец', '🔀 Сменить владельца', '✏️ Изменить долю',
    '📄 Получить документ', '📔 История', '✖️ Удалить владельца', '🚪 Выход'); # 👨‍💼 Владельцы

# Когда надо добавить новое здание/квартиру/владельца
newobjectmenu = get_button(1).add('🚪 Выход');

# БОТ
@bot.message_handler(content_types=['text', 'document', 'audio', 'photo'])
def get_text_messages(message):
    if message.text == '/start':
        bot.send_message(message.from_user.id, 'Добро пожаловать!', reply_markup = mainmenu);
        try:
            db.execute('INSERT INTO USERS VALUES(?, 1, "")', (message.from_user.id, ));
            bot.send_message(message.from_user.id, reply_markup = mainmenu);
        except:
            pass;

    step = db.execute('SELECT Step FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0][0];

    if message.text == '🚪 Выход':
        bot.send_message(message.from_user.id, 'Вы вернулись в главное меню', reply_markup = mainmenu);
        next_step(message.from_user.id, 1);

    elif message.text == '🔍 Поиск' and step == 1:
        text = 'Введите кадастровый номер, взяв один из следующего списка.\n\n'
        for i in db.execute('SELECT Kadastr, Address FROM BUILDINGS'):
            text += f'{i[0]}: {i[1]}\n';
        bot.send_message(message.from_user.id, text, reply_markup = newobjectmenu);
        next_step(message.from_user.id, 2);
    
    # ПОИСК ПО КАДАСТРОВОМУ НОМЕРУ
    elif step == 2:
        x = db.execute('SELECT * FROM BUILDINGS WHERE Kadastr = ?', (message.text, )).fetchall();
        if x == []:
            bot.send_message(message.from_user.id, '🚫 Ошибка: здание не найдено. Проверьте номер или добавьте новое.');
        else:
            x = x[0];
            text = building_text.replace('p', 'Нет') if x[14] == 0 else building_text.replace('p', 'Да');
            bot.send_photo(message.from_user.id, x[12], eval(text), reply_markup = buildingmenu);
            db.execute('UPDATE USERS SET Kadastr = ? WHERE Id = ?', (message.text, message.from_user.id, ));
            next_step(message.from_user.id, 3);

    # КВАРТИРЫ
    elif message.text == '🏠 Поиск квартиры' and step == 3:
        kad = db.execute('SELECT Kadastr FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0][0];
        text = 'Доступны следующие квартиры: ';
        sql_ = db.execute('SELECT Flat FROM FLATS WHERE Fid IN (SELECT Fid FROM RECORDS WHERE Kadastr = ?) GROUP BY Flat', (kad, )).fetchall();
        if len(sql_) != 0:
            for i in sql_:
                text += f'{i[0]}, ';
        if text == 'Доступны следующие квартиры: ':
            bot.send_message(message.from_user.id, 'Добавьте новую квартиру');
        else:
            bot.send_message(message.from_user.id, text[:-2], reply_markup = newobjectmenu);
            next_step(message.from_user.id, 4);

    elif step == 4:
        try:
            x = db.execute(flatsql, (message.text, message.from_user.id, )).fetchall();
            if x == []:
                bot.send_message(message.from_user.id, '🚫 Ошибка: квартира не найдена. Проверьте номер или добавьте новую.');
            else:
                x = x[0];
                bot.send_message(message.from_user.id, eval(flat_text), reply_markup = flatmenu);
                db.execute('UPDATE USERS SET Fid = ? WHERE Id = ?', (x[-1], message.from_user.id, ));
                next_step(message.from_user.id, 5);
        except Exception as e:
            print(e);
    
    # ВЛАДЕЛЬЦЫ
    elif message.text == '👨‍💼 Владельцы' and step == 5:
        text = 'Список владельцев:\n\n';
        c = 1;
        for i in db.execute('SELECT * FROM HOSTS WHERE Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?) AND IsActual = 1) GROUP BY FioHost',
            (message.from_user.id, )).fetchall():
            part = db.execute('SELECT Part FROM RECORDS WHERE Passport IN (SELECT Passport FROM HOSTS WHERE HOSTS.Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?))) AND Passport = ? AND IsActual = 1',
                (message.from_user.id, i[1], )).fetchall()[0][0];
            text += f'{c}. {i[0]}\nПаспортные данные: {i[1]}\nГод рождения: {i[2]}\nДоля в квартире: {part * 100}%\n\n';
            c += 1;
        if c == 1:
            text = 'У квартиры ещё нет владельцев.';
        bot.send_message(message.from_user.id, text, reply_markup = editownersmenu);
    
    elif message.text == '👨‍💼 Новый владелец':
        bot.send_message(message.from_user.id, 'Введите сообщение следующего образца:\n\n1. ФИО\n2. Паспортные данные (например: 18 08 3496)\n3. Год рождения\n4. Доля в квартире (без %)\n\nЕсли владелец вам уже известен, введите:\n2. Паспортные данные (например: 18 08 3496)\n4. Доля в квартире (без %)',
            reply_markup = newobjectmenu);
        next_step(message.from_user.id, 6);
    
    elif step == 6:
            kad, fid = db.execute('SELECT Kadastr, Fid FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0];
            info = [];
            for i in message.text.split('\n'):
                info.append(i[3:]);
            if db.execute('SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?) AND Passport = ? AND IsActual = 1',
                (message.from_user.id, info[0], )).fetchall() != []:
                bot.send_message(message.from_user.id, 'Указанный вами владелец уже владеет этой квартирой. Уточните данные.');
            elif len(info) == 2:
                x = db.execute('SELECT * FROM HOSTS WHERE Passport = ?', (info[0], )).fetchall();
                if x == []:
                    bot.send_message(message.from_user.id, 'Владелец не найден. Уточните данные.');
                else:
                    x = x[0];
                    bot.send_message(message.from_user.id, f'Данные о новом владельце:\n\n{x[0]}\n{x[1]}\n{info[1]}%');
                    part = float(info[1]) / 100;
                    txt = (f"Добавлен владелец {x[0]} ({x[1]}) с долей {info[1]}%");
                    passport = info[0];
            else:
                x = db.execute('SELECT * FROM HOSTS WHERE Passport = ?', (info[1], )).fetchall();
                if x == []:
                    db.execute('INSERT INTO HOSTS VALUES (?, ?, ?)', (info[0], info[1], info[2], ));
                    db.commit();
                    bot.send_message(message.from_user.id, f'Данные о новом владельце:\n\n{info[0]}\n{info[1]}\n{info[3]}%');
                    txt = (f"Добавлен владелец {info[0]} ({info[1]}) с долей {info[3]}%");
                else:
                    x = x[0];
                    bot.send_message(message.from_user.id, f'Данные о новом владельце:\n\n{x[0]}\n{x[1]}\n{info[3]}%');
                    txt = (f"Добавлен владелец {x[0]} ({x[1]}) с долей {info[3]}%");
                part = float(info[3]) / 100;
                passport = info[1];
            
            y = db.execute('SELECT Passport FROM RECORDS WHERE Fid = ? AND IsActual = 1', (fid, )).fetchall();
            if y[0][0] == None:
                db.execute('UPDATE RECORDS SET IsActual = 0 WHERE Fid = ?', (fid, ));
                db.execute('INSERT INTO RECORDS (Kadastr, Fid, Passport, Part, IsActual, BecameHost) VALUES (?, ?, ?, 1, 1, strftime("%d.%m.%Y"))',
                    (kad, fid, passport, ));
            elif len(y) == 1:
                y = db.execute('UPDATE RECORDS SET Part = Part - ? WHERE Fid = ? AND IsActual = 1',
                    (part, fid, ));
                db.execute(f'INSERT INTO RECORDS (Kadastr, Fid, Passport, Part, IsActual, BecameHost) VALUES (?, ?, ?, ?, 1, strftime("%d.%m.%Y"))',
                    (kad, fid, passport, part, ));
            else:
                rest = 1 - part;
                db.execute('UPDATE RECORDS SET Part = Part * ? WHERE Fid = ? AND IsActual = 1', (rest, fid, ));
                db.execute(f'INSERT INTO RECORDS (Kadastr, Fid, Passport, Part, IsActual, BecameHost) VALUES (?, ?, ?, ?, 1, strftime("%d.%m.%Y"))',
                    (kad, fid, passport, part, ));
            
            bot.send_message(message.from_user.id, 'Владелец успешно добавлен');
            # reply_markup = mainmenu
            # next_step(message.from_user.id, 1);

    elif message.text == '🔀 Сменить владельца':
        text = 'Выберите владельцев из списка:\n\n';
        c = 1;
        for i in db.execute('SELECT * FROM HOSTS WHERE Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?) AND IsActual = 1) GROUP BY FioHost',
            (message.from_user.id, )).fetchall():
            part = db.execute('SELECT Part FROM RECORDS WHERE Passport IN (SELECT Passport FROM HOSTS WHERE HOSTS.Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?))) AND Passport = ? AND IsActual = 1',
                (message.from_user.id, i[1], )).fetchall()[0][0];
            text += f'\n{c}. {i[0]}\nПаспортные данные: {i[1]}\nГод рождения: {i[2]}\nДоля в квартире: {part * 100}%\n';
            c += 1;
        text += '\nВведите по следующему образцу:\n\n1. Паспортные данные текущего владельца\n(2. ФИО)\n3. Паспортные данные нового владельца\n(4. Год рождения)';
        if c == 1:
            bot.send_message(message.from_user.id, 'У квартиры ещё нет владельцев');
        else:
            bot.send_message(message.from_user.id, text, reply_markup = newobjectmenu);
            next_step(message.from_user.id, 9);
    
    elif step == 9:
        try:
            info = [];
            for i in message.text.split('\n'):
                info.append(i[3:]);

            kad, fid = db.execute('SELECT Kadastr, Fid FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0];
            part = db.execute('SELECT Part FROM RECORDS WHERE Passport = ? AND IsActual = 1 AND Fid = ?',
                (info[0], fid, )).fetchall()[0][0];
            if len(info) == 2:
                x = db.execute('SELECT * FROM HOSTS WHERE Passport = ?', (info[0], )).fetchall();
                if x == []:
                    bot.send_message(message.from_user.id, 'Владелец не найден. Уточните данные.');
                else:
                    db.execute('UPDATE RECORDS SET IsActual = 0 WHERE Passport = ? AND Fid = ?', (info[0], fid, ));
                    if db.execute('SELECT count() FROM RECORDS WHERE Passport = ? AND IsActual = 1 AND Fid = ?', (info[1], fid, )).fetchall()[0][0] != 0:
                        db.execute(f'UPDATE RECORDS SET Part = Part + ? WHERE IsActual = 1 AND Fid = ? AND Passport = ?',
                            (part, fid, info[1], ));
                    else:
                        db.execute(f'INSERT INTO RECORDS (Kadastr, Fid, Passport, Part, IsActual, BecameHost) VALUES (?, ?, ?, ?, 1, strftime("%d.%m.%Y"))',
                            (kad, fid, info[1], part, ));
            elif len(info) == 4:
                x = db.execute('SELECT * FROM HOSTS WHERE Passport = ?', (info[1], )).fetchall();
                if x == []:
                    db.execute('INSERT INTO HOSTS VALUES (?, ?, ?)', (info[1], info[2], info[3],));
                    db.commit();
                db.execute('UPDATE RECORDS SET IsActual = 0 WHERE Passport = ? AND Fid = ?', (info[0], fid, ));
                if db.execute('SELECT count() FROM RECORDS WHERE Passport = ? AND IsActual = 1 AND Fid = ?', (info[1], fid, )).fetchall()[0][0] != 0:
                    db.execute(f'UPDATE RECORDS SET Part = Part + ? WHERE IsActual = 1 AND Fid = ? AND Passport = ?',
                        (part, fid, info[2], ));
                else:
                    db.execute(f'INSERT INTO RECORDS (Kadastr, Fid, Passport, Part, IsActual, BecameHost) VALUES (?, ?, ?, ?, 1, strftime("%d.%m.%Y"))',
                        (kad, fid, info[2], part, ));

            bot.send_message(message.from_user.id, f'Владелец сменён');
        except Exception as e:
            print(e, info);
            bot.send_message(message.from_user.id, 'Ошибка: повторите попытку.');

    elif message.text == '✏️ Изменить долю':
        text = 'Выберите владельцев из списка:\n\n';
        c = 1;
        for i in db.execute('SELECT * FROM HOSTS WHERE Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?) AND IsActual = 1) GROUP BY FioHost',
            (message.from_user.id, )).fetchall():
            part = db.execute('SELECT Part FROM RECORDS WHERE Passport IN (SELECT Passport FROM HOSTS WHERE HOSTS.Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?))) AND Passport = ? AND IsActual = 1',
                (message.from_user.id, i[1], )).fetchall()[0][0];
            text += f'{c}. {i[0]}\nПаспортные данные: {i[1]}\nГод рождения: {i[2]}\nДоля в квартире: {part * 100}%\n\n';
            c += 1;
        text += 'Введите по следующему образцу:\n\n1. Паспортные данные текущего владельца\n2. Число процентов (без %)';
        if c == 1:
            bot.send_message(message.from_user.id, 'У квартиры ещё нет владельцев');
        else:
            bot.send_message(message.from_user.id, text, reply_markup = newobjectmenu);
            next_step(message.from_user.id, 10);

    elif step == 10:
        try:
            kad, fid = db.execute('SELECT Kadastr, Fid FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0];
            info = [];
            for i in message.text.split('\n'):
                info.append(i[3:]);
            part = float(info[1]) / 100;
            if db.execute('SELECT count() FROM RECORDS WHERE Fid = ? AND IsActual = 1', (fid, )).fetchall()[0][0] - 1 != 0:
                rest = ((part - db.execute('SELECT Part FROM RECORDS WHERE Fid = ? AND Passport = ? AND IsActual = 1',
                    (fid, info[0], )).fetchall()[0][0]) /
                    (db.execute('SELECT count() FROM RECORDS WHERE Fid = ? AND IsActual = 1', (fid, )).fetchall()[0][0] - 1));
                db.execute('UPDATE RECORDS SET Part = ? WHERE Passport = ? AND Fid = ? AND IsActual = 1', (part, info[0], fid, ));
                db.commit();
                db.execute('UPDATE RECORDS SET Part = Part - ? WHERE Fid = ? AND Passport != ? AND IsActual = 1',
                    (rest, fid, info[0], ));
                bot.send_message(message.from_user.id, 'Доля изменена');
            else:
                bot.send_message(message.from_user.id, 'Вы единственный владелец квартиры');
        except:
            bot.send_message(message.from_user.id, 'Ошибка: повторите попытку.');
    
    elif message.text == '✖️ Удалить владельца':
        text = 'Выберите владельцев из списка:\n\n';
        c = 1;
        for i in db.execute('SELECT * FROM HOSTS WHERE Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?) AND IsActual = 1) GROUP BY FioHost',
            (message.from_user.id, )).fetchall():
            part = db.execute('SELECT Part FROM RECORDS WHERE Passport IN (SELECT Passport FROM HOSTS WHERE HOSTS.Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?))) AND Passport = ? AND IsActual = 1',
                (message.from_user.id, i[1], )).fetchall()[0][0];
            text += f'{c}. {i[0]}\nПаспортные данные: {i[1]}\nГод рождения: {i[2]}\nДоля в квартире: {part * 100}%\n\n';
            c += 1;
        text += 'Введите по следующему образцу:\n\nПаспортные данные текущего владельца'
        if c == 1:
            bot.send_message(message.from_user.id, 'У квартиры ещё нет владельцев');
        else:
            bot.send_message(message.from_user.id, text, reply_markup = newobjectmenu);
            next_step(message.from_user.id, 11);

    elif step == 11:
        try:
            kad, fid = db.execute('SELECT Kadastr, Fid FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0];
            part = db.execute('SELECT Part FROM RECORDS WHERE Fid = ? AND Passport = ? AND IsActual = 1',
                (fid, message.text, )).fetchall()[0][0];
            if len(db.execute('SELECT Part FROM RECORDS WHERE Fid = ? AND Passport != ? AND IsActual = 1',
                (fid, message.text, )).fetchall()) != 0:
                info = (part /
                    (len(db.execute('SELECT Part FROM RECORDS WHERE Fid = ? AND IsActual = 1', (fid, )).fetchall()) - 1));
                db.execute('UPDATE RECORDS SET IsActual = 0 WHERE Fid = ? And IsActual = 1 AND Passport = ?',
                    (fid, message.text, ));
                db.execute('UPDATE RECORDS SET Part = Part + ? WHERE Fid = ? AND IsActual = 1',
                    (info, fid, ));
                bot.send_message(message.from_user.id, 'Владелец удалён');
            else:
                bot.send_message(message.from_user.id, 'Владелец не найден. Уточните данные');
        except Exception as e:
            print(e);
            bot.send_message(message.from_user.id, 'Ошибка: повторите попытку.');
    
    elif message.text == '📔 История':
        kad, fid = db.execute('SELECT Kadastr, Fid FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0];
        text = 'Прошедшие владельцы квартиры по хронологии:\n';
        for i in db.execute('SELECT DISTINCT FioHost, HOSTS.Passport, Part FROM HOSTS, RECORDS WHERE HOSTS.Passport IN (SELECT Passport FROM RECORDS WHERE Fid = ? AND IsActual = 0) AND Part IN (SELECT Part FROM RECORDS WHERE Fid = ? AND IsActual = 0)',
            (fid, fid, )):
            text += f'\n{i[0]} ({i[1]}): {i[2] * 100}%';
        if text == 'Прошедшие владельцы квартиры по хронологии:\n':
            bot.send_message(message.from_user.id, 'У квартиры ещё нет владельцев.');
        else:
            bot.send_message(message.from_user.id, text);

    elif message.text == '➕ Новая квартира':
        bot.send_message(message.from_user.id, new_flat, reply_markup = newobjectmenu);
        next_step(message.from_user.id, 12);

    elif step == 12:
        try:
            info = [];
            for i in message.text.split('\n'):
                info.append(i[3:]);
            kad = db.execute('SELECT Kadastr FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0][0];
            mstorey, mflat = db.execute('SELECT Flow, Flats FROM BUILDINGS WHERE Kadastr = ?', (kad, )).fetchall()[0];
            if int(info[0]) <= mstorey and int(info[1]) <= mflat:
                db.execute('INSERT INTO FLATS (Storey, Flat, Rooms, Squareflat, Dwell, Branch, Balcony, Height) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (info[0], info[1], info[2], float(info[3]) + float(info[4]) + float(info[5]),
                        float(info[3]), float(info[4]), float(info[5]), float(info[6]), ));
                db.commit();
                fid = db.execute('SELECT Fid FROM FLATS ORDER BY Fid DESC LIMIT 1').fetchall()[0][0];
                db.execute('INSERT INTO RECORDS (Kadastr, Fid, Part, IsActual, BecameHost) VALUES (?, ?, ?, ?, strftime("%d.%m.%Y"))',
                    (kad, fid, 1, 1, ));
                db.commit();
                bot.send_message(message.from_user.id, 'Квартира успешно добавлена');
            else:
                bot.send_message(message.from_user.id, 'Ошибка: вы ввели этаж или номер квартиры больше количества этажей или квартир в доме.')
        except Exception as e:
            print(e);
            bot.send_message(message.from_user.id, 'Ошибка: повторите попытку.');

    elif message.text == '📝 Редактировать':
        bot.send_message(message.from_user.id, 'Выберите опцию', reply_markup = editbuildingmenu);
        '🗒 Примечание';

    elif message.text == '🖼 Картинка':
        bot.send_message(message.from_user.id, 'Выкиньте картинку в чат для смены изображения', reply_markup = newobjectmenu);
        next_step(message.from_user.id, 13);
    
    elif step == 13:
        try:
            bot.send_message(message.from_user.id, 'Изображение успешно изменено');
            kad = db.execute('SELECT Kadastr FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0][0];
            db.execute('UPDATE BUILDINGS SET Picture = ? WHERE Kadastr = ?', (message.photo[0].file_id, kad, ));
        except:
            bot.send_message(message.from_user.id, 'Ошибка: повторите попытку.');

    elif message.text == '🗒 Примечание':
        bot.send_message(message.from_user.id, 'Введите текст для примечания', reply_markup = newobjectmenu);
        next_step(message.from_user.id, 14);
    
    elif step == 14:
        try:
            bot.send_message(message.from_user.id, 'Примечание успешно изменено');
            kad = db.execute('SELECT Kadastr FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0][0];
            db.execute('UPDATE BUILDINGS SET Comment = ? WHERE Kadastr = ?', (message.text, kad, ));
        except:
            bot.send_message(message.from_user.id, 'Ошибка: повторите попытку.');

    elif message.text == '➕ Новое здание':
        bot.send_message(message.from_user.id, new_building, reply_markup = newobjectmenu);
        next_step(message.from_user.id, 15);

    elif step == 15:
        try:
            info = [];
            for i in message.text.split('\n'):
                if i[2] == ' ':
                    info.append(i[3:]);
                else:
                    info.append(i[4:]);

            boolean_ = 1 if info[-1] == 'Да' else 0; 
            db.execute('INSERT INTO BUILDINGS (Kadastr, Address, District, Land, Year, Material, Base, Wear, Flow, Line, Square, Flats, Elevator) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (info[0], info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8], info[9], info[10], info[11], boolean_));
            bot.send_message(message.from_user.id, 'Здание успешно добавлено');
        except:
            bot.send_message(message.from_user.id, 'Ошибка: повторите попытку.');

    elif message.text == '📄 Получить документ':
        text = 'Выберите владельцев из списка:\n';
        c = 1;
        for i in db.execute('SELECT * FROM HOSTS WHERE Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?) AND IsActual = 1) GROUP BY FioHost',
            (message.from_user.id, )).fetchall():
            part = db.execute('SELECT Part FROM RECORDS WHERE Passport IN (SELECT Passport FROM HOSTS WHERE HOSTS.Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?))) AND Passport = ? AND IsActual = 1',
                (message.from_user.id, i[1], )).fetchall()[0][0];
            text += f'\n{c}. {i[0]}\nПаспортные данные: {i[1]}\nГод рождения: {i[2]}\nДоля в квартире: {part * 100}%\n';
            c += 1;
        text += '\nВведите по следующему образцу:\n\nПаспортные данные текущего владельца';
        if c == 1:
            bot.send_message(message.from_user.id, 'У квартиры ещё нет владельцев');
        else:
            bot.send_message(message.from_user.id, text, reply_markup = newobjectmenu);
            next_step(message.from_user.id, 16);

    elif step == 16:
        try:
            kad, fid = db.execute('SELECT Kadastr, Fid FROM USERS WHERE Id = ?', (message.from_user.id, )).fetchall()[0];
            doc = DocxTemplate('tmp.docx');
            
            host = db.execute('SELECT * FROM HOSTS WHERE Passport = ?', (message.text, )).fetchall()[0];
            part = db.execute('SELECT Part FROM RECORDS WHERE Passport IN (SELECT Passport FROM HOSTS WHERE HOSTS.Passport IN (SELECT Passport FROM RECORDS WHERE Fid IN (SELECT Fid FROM USERS WHERE Id = ?))) AND Passport = ? AND IsActual = 1',
                (message.from_user.id, message.text, )).fetchall()[0][0];
            building = db.execute('SELECT * FROM BUILDINGS WHERE Kadastr = ?', (kad, )).fetchall()[0];
            flatinfo = db.execute('SELECT * FROM FLATS WHERE Fid = ?', (fid, )).fetchall()[0];
            context = {
                'fio': host[0],
                'passport': message.text,
                'address': building[1],
                'part': part * 100,
                'flat': flatinfo[2],
                'storey': flatinfo[1],
                'rooms': flatinfo[3],
                'squareflat': flatinfo[4],
                'dwell': flatinfo[5],
                'branch': flatinfo[6],
                'balcony': flatinfo[7],
                'height': flatinfo[8],
                'kad': kad,
                'district': building[2],
                'land': building[3],
                'year': building[4],
                'material': building[5],
                'base': building[6],
                'wear': building[8],
                'flow': building[9],
                'line': building[10],
                'square': building[11],
                'flats': building[13],
                'elevator': 'Да' if building[-1] == 1 else 'Нет',
                'comment': building[7],
                'date': dt.today().strftime('%d.%m.%Y')
            }
            doc.render(context);
            buffer = BytesIO();
            doc.save(buffer);
            buffer.seek(0);
            bot.send_document(message.from_user.id, buffer, caption = 'Документ успешно сгенерирован!', visible_file_name = f'{host[0]}.docx');
        except:
            bot.send_message(message.from_user.id, 'Вы ввели неверные паспортные данные');

    try:
        db.commit();
    except Exception as e:
        pass;

bot.polling(none_stop = True, interval = 0);