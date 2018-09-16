import telebot
import dbwork
import time
import settings
import datetime
import re
import cherrypy

_users = {}
_bot = telebot.TeleBot(settings.TOKEN)
_reg_exp = ['fuck']
TIME_LAUNCH = time.time()  # time launch bot
TIME_WELCOME = 2  # period time in seconds for welcome users (how often)
TIME_BAN_UNIX = 10  # period time in seconds for ban without activity user (how long)


class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.age = None
        self.sex = None
        self.email = None
        self.busy = None
        self.city = None
        self.date_msg = None
        self.date_msg_unix = None


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            _bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


def run():
    db = dbwork.DataBase()

    def send_welcome(message):
        try:
            bot_name = _bot.get_me().username
            _bot.send_message(message.chat.id,
                              'Здравствуйте, я администратор группы! '
                              '\nЧтобы стать членом нашей команды, нажмите на ссылку ниже!'
                              + 'https://t.me/' + bot_name + '?start')
            return 0
        except Exception:
            _bot.send_message(message.chat.id, 'Что-то пошло не так, пожалуйста, сообщите другому администратору'
                                               ' о вашей проблеме. Извините за неудобство.')

    @_bot.message_handler(content_types=["left_chat_member"])
    def left_user(message):
        try:
            db.delete_user(message.left_chat_member.id)
        except Exception:
            pass

    @_bot.message_handler(commands=['start'])
    def init_dialog(message):
        try:
            if message.chat.id == settings.GROUP_ID:
                check_in_db(message)
            else:
                if db.check_user(message.from_user.id):
                    _bot.send_message(message.from_user.id, 'Ты уже есть в нашей базе данных тебе не требуется'
                                                            ' вводить данную команду!')
                    return 0
                msg = _bot.reply_to(message, "Мы рады приветствовать тебя в нашей группе! Как тебя зовут?")
                _bot.register_next_step_handler(msg, process_name_step)
        except Exception:
            pass

    def process_name_step(message):
        try:
            uid = message.from_user.id
            name = message.text
            user = User(uid, name)
            _users[uid] = user
            msg = _bot.reply_to(message, 'Сколько тебе лет? ')
            _bot.register_next_step_handler(msg, process_age_step)
        except Exception as e:
            _bot.reply_to(message,
                          'Что-то пошло не так с вашим возрастом! '
                          'Сообщите любому другому администратору о своей проблеме.')

    def process_age_step(message):
        try:
            age = message.text
            if not age.isdigit():
                msg = _bot.reply_to(message, 'Возраст должен быть введен корректным числом. Сколько тебе лет? ')
                _bot.register_next_step_handler(msg, process_age_step)
                return
            if int(age) > 100 or int(age) < 3:
                msg = _bot.reply_to(message, 'Неккоректный возраст. Сколько тебе лет? ')
                _bot.register_next_step_handler(msg, process_age_step)
                return

            user = _users[message.from_user.id]
            user.age = age

            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
            markup.add('Женщина', 'Мужчина')
            msg = _bot.reply_to(message, 'Выбери свой пол: ', reply_markup=markup)
            _bot.register_next_step_handler(msg, process_sex_step)
        except Exception as e:
            _bot.reply_to(message,
                          'Что-то пошло не так с Вашим возрастом! '
                          'Сообщите любому другому администратору о своей проблеме или введи команду /start.')

    def process_sex_step(message):
        try:
            sex = message.text
            user = _users[message.from_user.id]
            if (sex == u'Женщина') or (sex == u'Мужчина'):
                user.sex = sex
            else:
                raise Exception()

            msg = _bot.reply_to(message, 'Введите Вашу электронную почту: ')
            _bot.register_next_step_handler(msg, process_email_step)

        except Exception as e:
            _bot.reply_to(message,
                          'Что-то пошло не так с Вашим полом! '
                          'Сообщите любому другому администратору о своей проблеме или введите команду: /start.')

    def process_email_step(message):
        try:
            user = _users[message.from_user.id]
            user.email = message.text

            msg = _bot.reply_to(message, 'Напишите кратко о Вашей нише, например "Занимаюсь металопрокатом" :')
            _bot.register_next_step_handler(msg, process_business_step)

        except Exception as e:
            _bot.reply_to(message,
                          'Что-то не так с Вашей почтой! '
                          'Сообщите любому другому администратору о своей проблеме или введите команду: /start.')

    def process_business_step(message):
        try:
            user = _users[message.from_user.id]
            user.busy = message.text
            msg = _bot.reply_to(message, 'В каком городе Вы живете?')
            _bot.register_next_step_handler(msg, process_city_step)
        except Exception as e:
            _bot.reply_to(message, 'Что-то не так с Вашей нишей! '
                                   'Сообщите любому другому администратору о своей проблеме.')

    def process_city_step(message):
        try:
            user = _users[message.from_user.id]
            user.city = message.text
            time_now = time.time()
            user.date_msg = str(datetime.datetime.fromtimestamp(time_now).strftime('%Y-%m-%d %H:%M:%S'))
            user.date_msg_unix = time_now
            db.push_user(user)

            _bot.send_message(message.from_user.id, 'Мы рады познакомиться с тобой, ' + user.name
                              + '!'
                                '\nНиже приведены правила нашего сообщества, которые нельзя нарушать.'
                                '\nВнимательно прочитайте их перед использованием чата.'
                                '\n1. Запрещено использовать любую рекламу и ненормативную лексику!'
                                '\n2. Пользователи не проявляющие активность более 3-х дней будут удалены!'
                                '\n3. Запрещен любой спам и флуд!')
            _users.clear()
        except Exception as e:
            _bot.reply_to(message, 'Что-то не так с Вашим городом! '
                                   'Сообщите любому другому администратору о своей проблеме.')

    # --------------------------------------- mass messages for admin  -------------------------------------------------
    @_bot.message_handler(commands=['settings'], func=lambda message: message.chat.id != settings.GROUP_ID)
    def setting(message):
        try:
            admins = _bot.get_chat_administrators(settings.GROUP_ID)
            for u in admins:
                if message.from_user.id == u.user.id:
                    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
                    markup.add('Рассылка', 'Добавить RegExp')

                    msg = _bot.reply_to(message, 'Доступ разрешен, так как Вы администратор группы.'
                                                 '\nВыберите режим работы:', reply_markup=markup)
                    _bot.register_next_step_handler(msg, define_mode)
                    break
        except Exception as exc:
            _bot.send_message(message.from_user.id, 'Что-то случилось в функциии setting')

    def define_mode(message):
        try:
            if message.text == u'Рассылка':
                msg = _bot.reply_to(message, 'Введите Ваше сообщение для рассылка и нажми Enter:')
                _bot.register_next_step_handler(msg, mass_notify)
            elif message.text == u'Добавить RegExp':
                msg = _bot.reply_to(message, 'Введите Ваше регулярное выражение:')
                _bot.register_next_step_handler(msg, add_regexp)
        except Exception as exc:
            _bot.send_message(message, "Что-то случилось в функции define_mode")

    def add_regexp(message):
        try:
            _reg_exp.append(message.text)
            _bot.send_message(message.chat.id, 'Регулярное выражение добавлено!')
        except Exception as exc:
            _bot.send_message(message.chat.id, 'Что-то пошло не так!')

    def mass_notify(message):
        try:
            id_rows = db.get_users_id()

            flag = 0
            for uid in id_rows:
                _bot.send_message(uid[0], message.text)
                if flag > 28:
                    flag = 0
                    time.sleep(1)
                flag += 1
            _bot.send_message(message.chat.id, 'Ваше сообщение разослано по всем пользователям группы.')
        except Exception as exc:
            print("Error! Function mass_notify don't work!")

    # --------------------------------------- bot ban --------------------------------------------------------------
    def moderate(message):
        try:
            for regexp in _reg_exp:
                if re.findall(regexp, message.text):
                    _bot.delete_message(message.chat.id, message.message_id)
                    _bot.send_message(message.from_user.id,
                                      'Вы получаете временный бан за использование ненормативной лексики или рекламы')
                    # bot.restrict_chat_member(message.chat.id, message.from_user.id, until_date=time.time() + 360)
        except Exception as exc:
            print("Error! Function moderate() don't work!")

    # ---------------------------------------------- delete links ------------------------------------------------------

    @_bot.message_handler(
        func=lambda message: message.entities is not None and message.chat.id == settings.GROUP_ID)
    def delete_links(message):
        try:
            for entity in message.entities:
                if entity.type in ["url", "text_link"]:
                    check_time_ban(message)  # -----------------for testing
                    _bot.send_message(message.from_user.id, 'Ссылки в нашей группе запрещены, в связи с чем, '
                                                            'Ваше сообщение было удалено!')
                    _bot.delete_message(message.chat.id, message.message_id)
                else:
                    return
        except Exception as exc:
            print("Error! delete_links don't work!")

    # ------------------------------------------ read all messages -----------------------------------------------------
    @_bot.message_handler(func=lambda message: message.text and message.chat.id == settings.GROUP_ID)
    def check_in_db(message):
        try:
            if db.check_user(message.from_user.id):
                db.push_date_msg(message.date, message.from_user.id)
                moderate(message)
                return 1
            _bot.delete_message(message.chat.id, message.message_id)
            check_time_welcome(message)
        except Exception as exc:
            print("Error! check_in_db don't work")

    def check_time_welcome(message):
        try:
            global TIME_LAUNCH
            time_now = time.time()
            if time_now > TIME_LAUNCH + TIME_WELCOME:
                TIME_LAUNCH = time_now
                send_welcome(message)
                check_time_ban(message)
        except Exception as exc:
            print("Error! check_time_welcome don't work!")

    def check_time_ban(message):
        try:
            users_id = db.get_ban_users(TIME_BAN_UNIX)
            for uid in users_id:
                _bot.send_message(uid[0],
                                  'Вы были удалены из группы, в связи с отсутствием активности в чате более 3-х дней!')
                _bot.kick_chat_member(settings.GROUP_ID, uid[0])
                db.delete_user(message.left_chat_member.id)
        except Exception as exc:
            print("Error! check_time_ban don't work!")

    _bot.remove_webhook()
    
    _bot.set_webhook(url=settings.WEBHOOK_URL_BASE + settings.WEBHOOK_URL_PATH,
                     certificate=open(settings.WEBHOOK_SSL_CERT, 'r'))
    
    cherrypy.config.update({
        'server.socket_host': settings.WEBHOOK_LISTEN,
        'server.socket_port': settings.WEBHOOK_PORT,
        'server.ssl_module': 'builtin',
        'server.ssl_certificate': settings.WEBHOOK_SSL_CERT,
        'server.ssl_private_key': settings.WEBHOOK_SSL_PRIV
    })

    cherrypy.quickstart(WebhookServer(), settings.WEBHOOK_URL_PATH, {'/': {}})

    # _bot.polling(none_stop=True, timeout=30)


if __name__ == '__main__':
    run()
