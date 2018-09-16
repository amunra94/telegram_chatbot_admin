import datetime
import sqlalchemy
import time
import sqlite3

TAB_USERS = 'users'
DATABASE = 'database.sqlite'


class DataBase:
    def __init__(self):
        self.engine = sqlalchemy.create_engine('sqlite:///' + DATABASE, echo=False)
        self.metadata = sqlalchemy.MetaData()
        self.users_table = sqlalchemy.Table(TAB_USERS, self.metadata,
                                       sqlalchemy.Column('user_id', sqlalchemy.Integer, primary_key=True),
                                       sqlalchemy.Column('name', sqlalchemy.String),
                                       sqlalchemy.Column('age', sqlalchemy.Integer),
                                       sqlalchemy.Column('sex', sqlalchemy.String),
                                       sqlalchemy.Column('email', sqlalchemy.String),
                                       sqlalchemy.Column('busy', sqlalchemy.String),
                                       sqlalchemy.Column('city', sqlalchemy.String),
                                       sqlalchemy.Column('date_msg', sqlalchemy.String),
                                       sqlalchemy.Column('date_msg_unix', sqlalchemy.Float)
                                       )

        self.metadata.create_all(bind=self.engine)

    def push_user(self, user):
        with self.engine.connect() as conn:
            meta = sqlalchemy.MetaData(self.engine)
            users_table = sqlalchemy.Table(TAB_USERS, meta, autoload=True)

            conn.execute(users_table.insert(),
                         user_id=user.user_id,
                         name=user.name,
                         age=user.age,
                         sex=user.sex,
                         email=user.email,
                         busy=user.busy,
                         city=user.city,
                         date_msg=user.date_msg,
                         date_msg_unix=user.date_msg_unix
                         )

    def delete_user(self, uid):
        with self.engine.connect() as conn:
            meta = sqlalchemy.MetaData(self.engine)
            users_table = sqlalchemy.Table(TAB_USERS, meta, autoload=True)
            conn.execute(users_table.delete(users_table.c.user_id == uid))

    def check_user(self, uid):
        with self.engine.connect() as conn:
            meta = sqlalchemy.MetaData(self.engine)
            users_table = sqlalchemy.Table(TAB_USERS, meta, autoload=True)
            t_uid = (uid,)
            records = conn.execute(sqlalchemy.select([users_table.c.user_id]).where(users_table.c.user_id == uid))

            if t_uid in records:
                return True
            else:
                return False

    def push_date_msg(self, time, uid):
        with self.engine.connect() as conn:
            meta = sqlalchemy.MetaData(self.engine)
            users_table = sqlalchemy.Table(TAB_USERS, meta, autoload=True)
            date = str(datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S'))
            conn.execute(
                users_table.update().where(users_table.c.user_id == uid).values(date_msg=date, date_msg_unix=utime))

    def get_users_id(self):
        with self.engine.connect() as conn:
            meta = sqlalchemy.MetaData(self.engine)
            users_table = sqlalchemy.Table(TAB_USERS, meta, autoload=True)
            records = conn.execute(sqlalchemy.select([users_table.c.user_id]))
            rows = list(records)
        return rows

    def get_ban_users(self, time_ban):
        with self.engine.connect() as conn:
            meta = sqlalchemy.MetaData(self.engine)
            users_table = sqlalchemy.Table(TAB_USERS, meta, autoload=True)
            time_now = time.time()
            records = conn.execute(
                sqlalchemy.select([users_table.c.user_id]).where(users_table.c.date_msg_unix < time_now - time_ban))
            rows = list(records)
        return rows

