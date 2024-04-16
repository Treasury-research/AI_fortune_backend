import mysql.connector
from dbutils.pooled_db import PooledDB
from urllib.parse import urlparse
from datetime import datetime, timedelta
import uuid
import pymysql
import os
import logging

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
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), gender=VALUES(gender), name=VALUES(name), account=VALUES(account)
                """
            cursor.execute(sql, (user_id, account, birthday, gender, name))
        self.db.commit()

    def select_user(self,user_id=None, birthday=None, gender=None, name=None,account=None):
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

    def select_user_id(self, account):
        params = {'account': account}  # 使用字典来传递参数
        sql = f"SELECT id FROM AI_fortune_user_test WHERE account=%(account)s"
        with self.db.cursor() as cursor:
            # 执行查询
            cursor.execute(sql, params)
            # 获取查询结果
            result = cursor.fetchone()
        return result
    def update_infos_in_to_asset(self, matcher_id,bazi_info,bazi_info_gpt,first_reply):
        """
            更新资产信息中的八字信息
        """
        with self.db.cursor() as cursor:
            sql = "UPDATE AI_fortune_assets_test SET bazi_info = %s, bazi_info_gpt = %s, first_reply = %s WHERE id=%s"
            cursor.execute(sql, (bazi_info, bazi_info_gpt, first_reply,matcher_id))
        self.db.commit()


    def select_infos_byid(self, matcher_id):
        """
            查询资产信息中的八字信息
        """
        # with self.db.cursor() as cursor:
        #     sql = "select bazi_info, bazi_info_gpt, first_reply  FROM AI_fortune_assets_test WHERE id=%s"
        #     cursor.execute(sql, (matcher_id))
        # self.db.commit()
        sql = "select bazi_info, bazi_info_gpt, first_reply  FROM AI_fortune_assets_test WHERE id=%s"
        with self.db.cursor() as cursor:
            # 执行查询
            cursor.execute(sql, matcher_id)
            # 获取查询结果
            result = cursor.fetchone()
        # 如果查询结果不为 None，则返回结果
        if result is not None:
            return result
        else:
            # 如果查询结果为 None，则返回三个空数组
            return [None,None,None]

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
                select_sql = "SELECT bazi_id, user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply, assistant_id, matcher_id, matcher_type FROM AI_fortune_bazi_chat_test WHERE conversation_id = %s OR bazi_id = %s ORDER BY createdAt DESC"
                cursor.execute(select_sql, (conversation_id, bazi_id))
                result = cursor.fetchone()
                if result:
                    bazi_id, user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply, assistant_id, matcher_id, matcher_type = result
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

    def select_bazi_id(self, conversation_id=None, matcher_id=None, user_id=None):
        with self.db.cursor() as cursor:
            if matcher_id:
                sql = "SELECT bazi_id FROM AI_fortune_bazi_chat_test WHERE matcher_id=%s AND conversation_id=%s"
                cursor.execute(sql, (matcher_id,conversation_id))
            elif user_id is not None:
                sql = "SELECT bazi_id FROM AI_fortune_bazi_chat_test WHERE user_id=%s"
                cursor.execute(sql, (user_id))
            else:
                sql = "SELECT bazi_id FROM AI_fortune_bazi_chat_test WHERE matcher_id IS NULL AND conversation_id=%s"
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
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), name= VALUES(name)
                        """
                    cursor.execute(sql, (id, name, birthday))
            self.db.commit()
            return True
        except:
            return None

    def update_asset_reply(self, name, first_reply):
        try:
            with connection.cursor() as cursor:
                sql = "UPDATE AI_fortune_assets_test SET first_reply = %s WHERE name = %s AND user_id IS NULL"
                cursor.executemany(insert_sql, first_reply, name)
            self.db.commit()
            return True
        except:
            return None

    def select_asset(self, user_id=None, matcher_id=None, hot=None, recent_hot=None):
        with self.db.cursor() as cursor:
            if hot and recent_hot:
                res = {}
                sql = "SELECT name, birthday, id FROM AI_fortune_assets_test WHERE hot=1"
                cursor.execute(sql, ())
                result = cursor.fetchall()
                res['hot'] = result
                sql = "SELECT name, birthday, id FROM AI_fortune_assets_test WHERE recent_hot=1"
                cursor.execute(sql, ())
                result = cursor.fetchall()
                res['recent_hot'] = result
                return res
            if matcher_id:
                sql = "SELECT name, birthday, report FROM AI_fortune_assets_test WHERE id=%s"
                cursor.execute(sql, (matcher_id,))
                result = cursor.fetchone()
                if result:
                    return result
                else:
                    return False
            else:
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

    def select_tg_bot_bazi_id(self,conversation_id):
        sql = f"SELECT bazi_id FROM AI_fortune_tg_bot_conversation_user_test WHERE conversation_id='{conversation_id}'".format(conversation_id)
        print(sql)
        with self.db.cursor() as cursor:
            # 执行查询
            cursor.execute(sql)
            # 获取查询结果
            result = cursor.fetchone()
        return result

    def select_tg_bot_bazi_info(self,bazi_id):
        sql = "SELECT bazi_id FROM AI_fortune_bazi_chat_test WHERE bazi_id= %s"
        with self.db.cursor() as cursor:
            # 执行查询
            cursor.execute(sql, (bazi_id))
            # 获取查询结果
            result = cursor.fetchone()
        return result
    
    def get_tg_bot_conversation(self,bazi_id):
        """
        data type:<class 'tuple'>
        data example:   (('我的运势怎么样', '你的运势...'), ('你好，我的八字是什么？', '根据你提供的知识...'))
        """
        with self.db.cursor() as cursor:
            sql = """
            SELECT human_message, AI_message FROM AI_fortune_conversation_test WHERE bazi_id = %s AND is_reset = 0 ORDER BY createdAt
            """
            cursor.execute(sql, (bazi_id))
            result = cursor.fetchall()
            if result:
                return result
            else:
                logging.info(f"No data in database, where conversation_id is{bazi_id}")
    
    def insert_conversation(self, conversation_id, human_message=None, AI_message=None, bazi_id=None, user_id=None):
        generated_uuid = str(uuid.uuid4())
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO AI_fortune_conversation_test (id, conversation_id, human_message, AI_message, bazi_id, user_id) VALUES (%s, %s, %s, %s, %s, %s)
                """
            cursor.execute(sql, (generated_uuid, conversation_id, human_message, AI_message, bazi_id,user_id))
        self.db.commit()
        logging.info(f"Insert conversation success where conversation_id = {conversation_id}")

    def get_conversation(self, conversation_id):
        """
        data type:<class 'tuple'>
        data example:   (('我的运势怎么样', '你的运势...'), ('你好，我的八字是什么？', '根据你提供的知识...'))
        """
        with self.db.cursor() as cursor:
            sql = """
            SELECT human_message, AI_message FROM AI_fortune_conversation_test WHERE conversation_id = %s AND is_reset = 0 ORDER BY createdAt
            """
            cursor.execute(sql, (conversation_id,))
            result = cursor.fetchall()
            if result:
                return result
            else:
                logging.info(f"No data in database, where conversation_id is{conversation_id}") 

    def reset_conversation(self, conversation_id=None, bazi_id=None):
        try:
            with self.db.cursor() as cursor:
                if bazi_id:
                    sql = "UPDATE AI_fortune_conversation_test SET is_reset = 1 bazi_id = %s"
                    cursor.execute(sql, (conversation_id, bazi_id, ))
                else:    
                    sql = "UPDATE AI_fortune_conversation_test SET is_reset = 1 WHERE conversation_id = %s"
                    cursor.execute(sql, (conversation_id,))
            self.db.commit()
            return True
        except:
            logging.info(f"database reset conversation error where conversation_id = {conversation_id}")
            return False

if __name__ == "__main__":
    tidb = TiDBManager()
    # res = tidb.select_chat_bazi(conversation_id="e1be7a32-5843-4b78-9eb5-06da9a5211c0",assistant_id=True,thread_id=True)
    # res = tidb.select_user_id(account='0x46B7D0b84Fd2e4Ac88fa9F8ad291De09C67C76C2')
    # res = tidb.update_reset_delete(conversation_id='ryen_test1111',reset=True)
    # res = tidb.select_chat_bazi(conversation_id="8ea31496-7a94-47d6-adc9-1089a710bf29",bazi_info=True)
    # print(res)
    # import uuid
    # id = str(uuid.uuid4())
    # res = tidb.upsert_asset(id=id, name="ERN",birthday="2021-1-29 14")
    res = tidb.select_asset(matcher_id="37cef2a4-3282-40dc-888a-464468c164ae")
    print(type(res[0]),type(res[1].hour))
