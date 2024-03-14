import mysql.connector
from dbutils.pooled_db import PooledDB
from urllib.parse import urlparse
from datetime import datetime, timedelta
import uuid
import pymysql
import os

username = os.environ["DBusername"]
password = os.environ["DBpassword"]
host = os.environ["DBhostname"]
port = os.environ["DBport"] 
database = os.environ["DBdbname"] 
config = {
    'user': username,
    'password': password,
    'host': host,
    'port': port,
    'database': database
}
# 连接池配置
pool = PooledDB(
    creator=pymysql,  # 使用的数据库模块
    maxconnections=10,  # 连接池最大连接数量
    mincached=2,       # 初始化时，连接池中至少创建的空闲的连接
    maxcached=5,       # 连接池中最多闲置的连接
    maxshared=3,       # 连接池中最多共享的连接数量
    blocking=True,     # 连接池中如果没有可用连接后是否阻塞等待
    host=host,
    port=int(port),
    user=username,
    password=password,
    database=database,
    ssl={"ssl_mode":"VERIFY_IDENTITY",
        "ssl_accept":"strict"
    }
)

class TiDBManager:
    def __init__(self):
        self.db = pool.connection()

    def upsert_user(self, user_id, birthday=None, gender=None, account=None, name=None):
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO AI_fortune_user_test (id, account, birthday, gender, name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), gender=VALUES(gender), name=VALUES(name), account=VALUES(account)
                """
            cursor.execute(sql, (user_id, account, birthday, gender, name))
        self.db.commit()

    def select_user(user_id, birthday=None, gender=None, name=None):
        fields = []  # 默认始终包含id字段
        params = {'user_id': user_id}  # 使用字典来传递参数
        # 根据参数决定是否包含特定字段
        if gender:
            fields.append('gender')
        if birthday:
            fields.append('birthday')
        if name:
            fields.append('name')
        fields_str = ', '.join(fields)
        sql = f"SELECT {fields_str} FROM AI_fortune_user_test WHERE id=%(user_id)s"
        with self.db.cursor() as cursor:
            # 执行查询
            cursor.execute(sql, params)
            # 获取查询结果
            result = cursor.fetchone()
        return result

    def insert_bazi_chat(self, user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply, assistant_id=None, thread_id=None, matcher_id=None, matcher_type=None, is_deleted=0):
        bazi_id = str(uuid.uuid4())
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO AI_fortune_bazi_chat_test (bazi_id, user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply, assistant_id, thread_id, matcher_id, matcher_type, is_deleted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            cursor.execute(sql, (bazi_id, user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply, assistant_id, thread_id, matcher_id, matcher_type, is_deleted))
        self.db.commit()
        return bazi_id

    def update_bazi(self, bazi_info, bazi_info_gpt, first_reply, conversation_id=None, bazi_id=None):
        with self.db.cursor() as cursor:
            sql = "UPDATE AI_fortune_bazi_chat_test SET bazi_info = %s, bazi_info_gpt = %s, first_reply = %s WHERE conversation_id = %s OR bazi_id = %s"
            cursor.execute(sql, (bazi_info, bazi_info_gpt, first_reply, conversation_id, bazi_id))
        self.db.commit()
 
    def update_chat(self, assistant_id, thread_id, conversation_id=None, bazi_id=None):
        with self.db.cursor() as cursor:
            sql = "UPDATE AI_fortune_bazi_chat_test SET assistant_id = %s, thread_id = %s WHERE conversation_id = %s OR bazi_id = %s"
            cursor.execute(sql, (assistant_id, thread_id, conversation_id, bazi_id))
        self.db.commit()

    def update_reset_delete(self, conversation_id=None, bazi_id=None, reset=None):
        with self.db.cursor() as cursor:
            # if reset; copy a new record
            sql = "UPDATE AI_fortune_bazi_chat_test SET is_deleted = 1 WHERE conversation_id = %s OR bazi_id = %s"
            cursor.execute(sql, (conversation_id, bazi_id))
            if reset:
                select_sql = "SELECT bazi_id, user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply, matcher_id, matcher_type FROM AI_fortune_bazi_chat_test WHERE conversation_id = %s OR bazi_id = %s"
                cursor.execute(select_sql, (conversation_id, bazi_id))
                result = cursor.fetchone()
                bazi_id, user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply, matcher_id, matcher_type = result
                self.insert_bazi_chat(user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply, assistant_id, None, matcher_id, matcher_type)
        self.db.commit()


    def select_chat_bazi(self,conversation_id=None, bazi_id=None, first_reply=None, bazi_info_gpt=None, bazi_info=None, matcher_id=None, assistant_id=None, thread_id=None):
        fields = []  # 默认始终包含id字段
        params = {'conversation_id': conversation_id, 'bazi_id': bazi_id}  # 使用字典来传递参数
        # 根据参数决定是否包含特定字段
        if first_reply:
            fields.append('first_reply')
        if bazi_info_gpt:
            fields.append('bazi_info_gpt')
        if bazi_info:
            fields.append('bazi_info')
        if matcher_id:
            fields.append('matcher_id')
        if assistant_id:
            fields.append('assistant_id')
        if thread_id:
            fields.append('thread_id')

        fields_str = ', '.join(fields)
        sql = f"SELECT {fields_str} FROM AI_fortune_bazi_chat_test WHERE conversation_id=%(conversation_id)s OR bazi_id=%(bazi_id)s"
        with self.db.cursor() as cursor:
            # 执行查询
            cursor.execute(sql, params)
            # 获取查询结果
            result = cursor.fetchone()
        return result

    def select_bazi_id(self, conversation_id=None, matcher_id=None):
        with self.db.cursor() as cursor:
            if matcher_id:
                sql = "SELECT id FROM AI_fortune_bazi_test WHERE matcher_id=%s AND conversation_id=%s"
                cursor.execute(sql, (matcher_id,conversation_id))
            else:
                sql = "SELECT id FROM AI_fortune_bazi_test WHERE matcher_id IS Null AND conversation_id=%s"
                cursor.execute(sql, (conversation_id))
            result = cursor.fetchone()
            if result:
                return result
            else:
                return None

    def upsert_matcherPerson(self, id, gender, birthday, user_id, name=None):
        with self.db.cursor() as cursor:
            sql = """
            INSERT INTO AI_fortune_matcherPerson_test (id, gender, birthday, user_id, name)
            VALUES (%s, %s, %s, %s,%s)
            ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), gender = VALUES(gender), name=VALUES(name), user_id=VALUES(user_id)
            """
            cursor.execute(sql, (id, gender, birthday, user_id, name))
        self.db.commit()

    def select_matcherPerson(self, user_id, id=None):
        with self.db.cursor() as cursor:
            if id:
                sql = "SELECT birthday FROM AI_fortune_matcherPerson_test WHERE id=%s"
                cursor.execute(sql, (id,))
                result = cursor.fetchone()
            else:
                sql = "SELECT gender, birthday, id, name FROM AI_fortune_matcherPerson_test WHERE user_id=%s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchall()
            if result:
                return result
            else:
                return False

    def upsert_asset(self, id, name, birthday,user_id=None):
        try:
            with self.db.cursor() as cursor:
                # 如果是用户自己导入的资产，那要带上user_id进行存储
                if user_id:
                    sql = """
                        INSERT INTO AI_fortune_assets_test (id, name, birthday, user_id)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), name= VALUES(name), user_id=VALUES(user_id)
                        """
                    cursor.execute(sql, (id, name, birthday,user_id))
                else:
                    sql = """
                        INSERT INTO AI_fortune_assets_test (id, name, birthday)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), name= VALUES(name)
                        """
                    cursor.execute(sql, (id, name, birthday))
            self.db.commit()
            return True
        except:
            return None

    def select_asset(self, user_id):
        with self.db.cursor() as cursor:
            sql = "SELECT name, birthday, id FROM AI_fortune_assets_test WHERE user_id=%s OR user_id IS NULL"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchall()
            if result:
                return result
            else:
                return False

    def insert_tg_bot_conversation_user(self, conversation_id, user_id, bazi_id):
    # 存储tg_bot 的conversation_id（即tg的chat_id）和user_id(后端生成的个人八字信息标志) 还有标志tg中个人或者配对的八字背景信息id
        generated_uuid = str(uuid.uuid4())
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO AI_fortune_tg_bot_conversation_user_test (id, conversation_id, user_id, bazi_id)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE bazi_id = VALUES(bazi_id), user_id=VALUES(user_id)
                """
            cursor.execute(sql, (generated_uuid,conversation_id, user_id, bazi_id))
        self.db.commit()
 
if __name__ == "__main__":
    tidb = TiDBManager()
    res = tidb.select_chat_bazi(conversation_id="e1be7a32-5843-4b78-9eb5-06da9a5211c0",assistant_id=True,thread_id=True)
    print(res)