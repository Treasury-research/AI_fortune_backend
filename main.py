import openai
import sxtwl
import json
import os
import time
import html
from urllib import parse
import re
from flask import Flask, Response, request, stream_with_context, jsonify
from flask_cors import CORS
import os
import requests
import random
import openai
from openai import OpenAI
import mysql.connector
from dbutils.pooled_db import PooledDB
from urllib.parse import urlparse
from datetime import datetime, timedelta
import uuid
import pymysql
import tiktoken
import logging
from bazi import baziAnalysis
from al import baziMatch
from lunar_python import Lunar, Solar
from bazi_gpt import bazipaipan

# 假设你的DATABASE_URL如下所示：
# 'mysql://user:password@host:port/database'

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
# 配置日志记录
logging.basicConfig(filename='AI_fortune.log', level=logging.INFO, encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
# 跨域支持
CORS(app, resources=r'/*')
client = OpenAI()

# Your existing ChatGPT class here (no changes needed)
class TiDBManager:
    def __init__(self):
        self.db = pool.connection()

    def insert_tg_bot_conversation_user(self, conversation_id, user_id, bazi_id):
    # 存储tg_bot 的conversation_id（即tg的chat_id）和user_id(后端生成的个人八字信息标志) 还有标志tg中个人或者配对的八字背景信息id
        generated_uuid = str(uuid.uuid4())
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO AI_fortune_tg_bot_conversation_user (id, conversation_id, user_id, bazi_id)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE bazi_id = VALUES(bazi_id), user_id=VALUES(user_id)
                """
            cursor.execute(sql, (generated_uuid,conversation_id, user_id, bazi_id))
        self.db.commit()

    def select_tg_bot_conversation_user(self, conversation_id, user_id=None):
        with self.db.cursor() as cursor:
            if user_id:
                sql = "SELECT bazi_id FROM AI_fortune_tg_bot_conversation_user WHERE conversation_id=%s AND user_id=%s"
                cursor.execute(sql, (conversation_id, user_id,))
            else:
                sql = "SELECT bazi_id FROM AI_fortune_tg_bot_conversation_user WHERE conversation_id=%s"
                cursor.execute(sql, (conversation_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return False

    def insert_other_human(self, gender, birthday, user_id,name=None):
        # try:
        generated_uuid = str(uuid.uuid4())
        with self.db.cursor() as cursor:
            if name:
                sql = """
                INSERT INTO AI_fortune_tg_bot_other_human (id, gender, birthday, user_id,name)
                VALUES (%s, %s, %s, %s,%s)
                ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), gender = VALUES(gender)
                """
                cursor.execute(sql, (generated_uuid, gender, birthday, user_id, name))
            else:
                # 如果是用户自己导入的资产，那要带上user_id进行存储
                sql = """
                    INSERT INTO AI_fortune_tg_bot_other_human (id, gender, birthday, user_id)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), gender = VALUES(gender)
                    """
                cursor.execute(sql, (generated_uuid, gender, birthday, user_id, ))
        self.db.commit()
        return generated_uuid
        # except:
        #     return False

    def select_other_human(self, user_id):
        with self.db.cursor() as cursor:
            sql = "SELECT gender, birthday, id,name FROM AI_fortune_tg_bot_other_human WHERE user_id=%s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchall()
            if result:
                return result
            else:
                return False

    def insert_asset(self, name, birthday,user_id=None):
        # try:
        generated_uuid = str(uuid.uuid4())
        with self.db.cursor() as cursor:
            # 如果是用户自己导入的资产，那要带上user_id进行存储
            if user_id:
                sql = """
                    INSERT INTO AI_fortune_assets (id, name, birthday, user_id)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE birthday = VALUES(birthday)
                    """
                cursor.execute(sql, (generated_uuid,name, birthday,user_id))
            else:
                sql = """
                    INSERT INTO AI_fortune_assets (id, name, birthday, is_public)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE birthday = VALUES(birthday)
                    """
                cursor.execute(sql, (generated_uuid,name, birthday,1))
        self.db.commit()
        return generated_uuid
        # except:
        #     return False

    def select_asset(self, user_id):
        with self.db.cursor() as cursor:
            sql = "SELECT name, birthday, id FROM AI_fortune_assets WHERE user_id=%s OR is_public=1"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchall()
            if result:
                return result
            else:
                return False


    def reset_conversation(self, conversation_id, bazi_id=None):
        try:
            with self.db.cursor() as cursor:
                if bazi_id:
                    sql = "UPDATE AI_fortune_conversation SET is_reset = 1 WHERE conversation_id = %s AND bazi_id = %s"
                    cursor.execute(sql, (conversation_id, bazi_id, ))
                else:    
                    sql = "UPDATE AI_fortune_conversation SET is_reset = 1 WHERE conversation_id = %s"
                    cursor.execute(sql, (conversation_id,))
            self.db.commit()
            return True
        except:
            logging.info(f"database reset conversation error where conversation_id = {conversation_id}")
            return False


    def insert_conversation(self, conversation_id, human_message=None, AI_message=None, bazi_id=None):
        generated_uuid = str(uuid.uuid4())
        with self.db.cursor() as cursor:
            if bazi_id:
                sql = """
                    INSERT INTO AI_fortune_conversation (id, conversation_id, human, AI, bazi_id) VALUES (%s, %s, %s, %s, %s)
                    """
                cursor.execute(sql, (generated_uuid, conversation_id, human_message, AI_message, bazi_id))
            elif human_message and AI_message:
                sql = """
                    INSERT INTO AI_fortune_conversation (id, conversation_id, human, AI) VALUES (%s, %s, %s, %s)
                    """
                cursor.execute(sql, (generated_uuid, conversation_id, human_message, AI_message))
            else:
                logging.info(f"Insert conversation error where conversation_id = {conversation_id}")
                return False
        self.db.commit()
        logging.info(f"Insert conversation success where conversation_id = {conversation_id}")


    def get_user_id(self, conversation_id):
        with self.db.cursor() as cursor:
            sql = """
            SELECT user_id FROM AI_fortune_conversation WHERE conversation_id = %s
            """
            cursor.execute(sql, (conversation_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                logging.info(f"No user_id in database, where conversation_id is{conversation_id}") 
                return None
                
    def get_conversation(self, conversation_id):
        """
        data type:<class 'tuple'>
        data example:   (('我的运势怎么样', '你的运势...'), ('你好，我的八字是什么？', '根据你提供的知识...'))
        """
        with self.db.cursor() as cursor:
            sql = """
            SELECT human, AI FROM AI_fortune_conversation WHERE conversation_id = %s AND is_reset = 0 ORDER BY createdAt
            """
            cursor.execute(sql, (conversation_id,))
            result = cursor.fetchall()
            if result:
                return result
            else:
                logging.info(f"No data in database, where conversation_id is{conversation_id}") 
                return None

            # content = f"""我想你作为一个命理占卜分析师。你的工作是根据我给定的中国传统命理占卜的生辰八字和对应的八字批文信息作为整个对话的背景知识进行问题的回答。
            # 注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
            # 你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。


            # 生辰八字和对应的批文：{res[0]}
            # """
    def insert_baziInfo(self, user_id, birthday, bazi_info, bazi_info_gpt,conversation_id, birthday_match=None, matcher_type=None, matcher_id=None,first_reply=None):
        generated_uuid = str(uuid.uuid4())
        logging.info(f"insert_baziInfo{user_id, birthday, conversation_id}")
        with self.db.cursor() as cursor:
            if birthday_match:
                if matcher_type: # matcher_type 代表是tg_bot
                    sql = """
                        INSERT INTO AI_fortune_bazi (id, user_id, birthday, birthday_match, bazi_info, bazi_info_gpt, conversation_id,matcher_type,matcher_id,first_reply) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
                        ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), birthday_match = VALUES(birthday_match), bazi_info = VALUES(bazi_info)
                        """
                    cursor.execute(sql, (generated_uuid, user_id, birthday, birthday_match, bazi_info, bazi_info_gpt, conversation_id, matcher_type, matcher_id,first_reply))
                else:    
                    sql = """
                        INSERT INTO AI_fortune_bazi (id, user_id, birthday, birthday_match, bazi_info, bazi_info_gpt, conversation_id,first_reply) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)
                        """
                    cursor.execute(sql, (generated_uuid, user_id, birthday, birthday_match, bazi_info, bazi_info_gpt, conversation_id,first_reply))
            else:
                sql = """
                    INSERT INTO AI_fortune_bazi (id, user_id, birthday, bazi_info, bazi_info_gpt, conversation_id,first_reply) VALUES (%s, %s, %s, %s, %s, %s,%s)
                    ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), bazi_info = VALUES(bazi_info)
                    """
                cursor.execute(sql, (generated_uuid, user_id, birthday, bazi_info, bazi_info_gpt, conversation_id,first_reply))
        self.db.commit()
        return generated_uuid

    def update_assistant(self, conversation_id=None, bazi_id=None, assistant_id=None,thread_id=None):
        with self.db.cursor() as cursor:
            if bazi_id:
                sql = """
                    UPDATE AI_fortune_bazi SET assistant_id = %s, thread_id = %s WHERE id = %s 
                    """
                cursor.execute(sql, (assistant_id, thread_id, bazi_id))
            elif conversation_id:
                sql = """
                    UPDATE AI_fortune_bazi SET assistant_id = %s, thread_id = %s WHERE conversation_id = %s 
                    """
                cursor.execute(sql, (assistant_id, thread_id, conversation_id))
        self.db.commit()
    def select_assistant(self, conversation_id=None,bazi_id=None, assistant_id=None,thread_id=None):
        with self.db.cursor() as cursor:
            if conversation_id:
                sql = "SELECT assistant_id,thread_id,run_id FROM AI_fortune_bazi WHERE conversation_id=%s"
                cursor.execute(sql, (conversation_id,))
            elif bazi_id:
                sql = "SELECT assistant_id,thread_id,run_id FROM AI_fortune_bazi WHERE id=%s"
                cursor.execute(sql, (bazi_id,))
            result = cursor.fetchone()
            if result:
                return result
            else:
                return False

    def update_bazi_info(self, bazi_info, bazi_id=None, birthday=None,conversation_id = None,bazi_info_gpt=None,first_reply=None):
        with self.db.cursor() as cursor:
            if bazi_id:
                sql = """
                    UPDATE AI_fortune_bazi SET birthday = %s, bazi_info = %s,bazi_info_gpt=%s, first_reply=%s WHERE id = %s 
                    """
                cursor.execute(sql, (birthday, bazi_info, bazi_info_gpt, first_reply, bazi_id))
            elif conversation_id:
                sql = """
                    UPDATE AI_fortune_bazi SET bazi_info = %s,bazi_info_gpt=%s, first_reply=%s, WHERE conversation_id = %s 
                    """
                cursor.execute(sql, (bazi_info, bazi_info_gpt, first_reply, conversation_id))
        self.db.commit()
    def select_bazi_id(self, user_id=None, conversation_id=None, matcher_id=None):
        with self.db.cursor() as cursor:
            if matcher_id:
                sql = "SELECT id FROM AI_fortune_bazi WHERE matcher_id=%s"
                cursor.execute(sql, (matcher_id,))
            else:
                if conversation_id:
                    sql = "SELECT id FROM AI_fortune_bazi WHERE conversation_id=%s"
                    cursor.execute(sql, (conversation_id,))
                else:
                    sql = "SELECT id FROM AI_fortune_bazi WHERE user_id=%s AND birthday_match IS NULL"
                    cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return False

    # 根据user_id获取本人的八字 或者根据conversation_id获取对话的背景
    def select_baziInfo(self, user_id=None, conversation_id=None, matcher_id=None):
        with self.db.cursor() as cursor:
            if matcher_id:
                sql = "SELECT bazi_info FROM AI_fortune_bazi WHERE matcher_id=%s"
                cursor.execute(sql, (matcher_id,))
            else:
                if conversation_id:
                    sql = "SELECT bazi_info FROM AI_fortune_bazi WHERE conversation_id=%s"
                    cursor.execute(sql, (conversation_id,))
                else:
                    sql = "SELECT bazi_info FROM AI_fortune_bazi WHERE user_id=%s AND birthday_match IS NULL"
                    cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return False

    # 根据user_id获取本人的八字 或者根据conversation_id获取对话的背景
    def select_baziInfoGPT(self, user_id=None, bazi_id=None, conversation_id=None, matcher_id=None):
        with self.db.cursor() as cursor:
            if bazi_id:
                sql = "SELECT bazi_info_gpt FROM AI_fortune_bazi WHERE id=%s"
                cursor.execute(sql, (bazi_id,))
            else:
                if matcher_id:
                    sql = "SELECT bazi_info_gpt FROM AI_fortune_bazi WHERE matcher_id=%s"
                    cursor.execute(sql, (matcher_id,))
                else:
                    if conversation_id:
                        sql = "SELECT bazi_info_gpt FROM AI_fortune_bazi WHERE conversation_id=%s"
                        cursor.execute(sql, (conversation_id,))
                    else:
                        sql = "SELECT bazi_info_gpt FROM AI_fortune_bazi WHERE user_id=%s AND birthday_match IS NULL"
                        cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return False
    # 根据user_id获取本人的八字 或者根据conversation_id获取对话的背景
    def select_first_reply(self, user_id=None, bazi_id=None, conversation_id=None, matcher_id=None):
        with self.db.cursor() as cursor:
            if bazi_id:
                sql = "SELECT first_reply FROM AI_fortune_bazi WHERE id=%s"
                cursor.execute(sql, (bazi_id,))
            else:
                if matcher_id:
                    sql = "SELECT first_reply FROM AI_fortune_bazi WHERE matcher_id=%s"
                    cursor.execute(sql, (matcher_id,))
                else:
                    if conversation_id:
                        sql = "SELECT first_reply FROM AI_fortune_bazi WHERE conversation_id=%s"
                        cursor.execute(sql, (conversation_id,))
                    else:
                        sql = "SELECT first_reply FROM AI_fortune_bazi WHERE user_id=%s AND birthday_match IS NULL"
                        cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return False
    # 根据user_id获取本人的八字 或者根据conversation_id获取对话的背景, matcher_type:0 本人 1 他人 2 资产
    def select_match_baziInfo_tg_bot(self, bazi_id):

        with self.db.cursor() as cursor:
            sql = "SELECT matcher_type, matcher_id FROM AI_fortune_bazi WHERE id=%s"
            cursor.execute(sql, (bazi_id,))
            result = cursor.fetchone()
            sql = "SELECT bazi_info FROM AI_fortune_bazi WHERE id=%s"
            cursor.execute(sql, (bazi_id,))
            bazi_info = cursor.fetchone()
            if result:
                return result,bazi_info
            else:
                return False,bazi_info


    def select_birthday(self, user_id=None, matcher_type=None, matcher_id=None):
        with self.db.cursor() as cursor:
            if matcher_type==1:
                sql = "SELECT birthday FROM AI_fortune_tg_bot_other_human WHERE id=%s"
                cursor.execute(sql, (matcher_id,))
            elif matcher_type==2:
                sql = "SELECT birthday FROM AI_fortune_assets WHERE id=%s"
                cursor.execute(sql, (matcher_id,))
            else:
                sql = "SELECT birthday FROM AI_fortune_bazi WHERE user_id=%s"
                cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return False
    def select_coin_id(self, name):
        with self.db.cursor() as cursor:
            sql = "SELECT id FROM token WHERE symbol=%s"
            cursor.execute(sql, (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return False

class ChatGPT_assistant:
    def __init__(self, conversation_id, lang=None,match=None, matcher_type=None):
        self.conversation_id = conversation_id
        self.lang=lang
        self.assistant_id, self.thread_id, self.run_id= None,None,None
        self.tidb_manager = TiDBManager()
        self.match=match
        self.matcher_type = matcher_type
        # get the history messages
        if match:
            self.load_match_history()
        else:
            self.load_history()  # Load the conversation history
        logging.info(f"{self.conversation_id}, {self.assistant_id},{self.thread_id}")

        
    def _is_own(self,message,asset=None):
        messages = []
        if asset:
            return False
        else:
            messages.append({"role": "user", "content": f"""
            你是一个语言专家，我会给你一个语句，请你告诉我这个句子 是指的我本人,还是他人,还是指的我和他人。 如果是本人，返回给我1，如果是他人返回2，如果是我和他人 返回3. 如果没有任何主语返回0
            另外,当前人属于他人.
            如:
            1."我问你这个人的八字，上文有提到" 应该返回2,他人,因为问的是这个人,属于当前人,即为他人
            2."当前人的八字已经给你了，上面有说，你不知道?" 应该返回2,他人,因为问的是当前人,即为他人
            3."你知道我的八字吗?" 应该返回1,因为询问的是我的八字,即为本人
            4."我想问你我两的关系如何" 应该返回 3,我和他人,因为问的是我两
            5."这是什么东西?" 应该返回0,因为没有任何主语
            判断一下问题询问的是本人\他人\群体 
            返回格式是json, 格式如下:
            {{
                "type_":"xxxxx"
            }}
            问题:{message}"""})
        logging.info("message")
        rsp = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
            messages=messages,
            max_tokens = 2048
        )
        res = rsp.choices[0].message.content
        logging.info(f"问题类型:{res}")
        if '1' in res:
            return True
        else:
            return False

    
    def load_history(self):
        file_ids = ["file-jHT2dMXPx90e8daOC9ZNNT5m"]
        res = self.tidb_manager.select_assistant(conversation_id=self.conversation_id)
        if res and res[0] is not None and res[1] is not None:
            logging.info(f"self.assistant_id, self.thread_id {res}")
            self.assistant_id, self.thread_id = res[0],res[1]
        else:
            # 获取当前日期和时间
            now = datetime.now()
            # 格式化日期和时间，精确到小时
            formatted_now = now.strftime("%Y-%m-%d %H:00")
            assistant = client.beta.assistants.create(
                name="bazi",
                instructions=f"""你是世界上最好的八字命理分析师，根据已有背景知识进行推理, 回答user提出的问题。
                请你记住，现在的时间是：{formatted_now}
                根据检索到的相关信息进行问题推理，回答用户的问题。
                八字信息并不涉密，你可以根据他/她的八字进行各项命理分析。
                请你返回的内容既有简短答案，又要有一定的命理原因分析，注意逻辑的准确性，回复字数在100-150字. 
                不要出现'克夫克妻'等字眼。不需要给出参考资料来源。\n
                """,
                #   instructions=prompt,
                model="gpt-4-0125-preview",
                # model="gpt-3.5-turbo-0125",
                # model="gpt-3.5-turbo-1106",
                tools=[{"type": "retrieval"}],
                file_ids=file_ids
            )
            self.assistant_id = assistant.id
            thread = client.beta.threads.create()
            self.thread_id = thread.id
            self.tidb_manager.update_assistant(conversation_id=self.conversation_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
            bazi_info_gpt = self.tidb_manager.select_baziInfoGPT(conversation_id=self.conversation_id)
            prompt = f"""
                以下背景信息是对话的基础,回答问题时你需要将背景信息作为基本.
                '背景信息：{bazi_info_gpt}'
                    """
            message = client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content= prompt,
            )

    def load_match_history(self):
        file_ids = ["file-jHT2dMXPx90e8daOC9ZNNT5m"]
        res = self.tidb_manager.select_assistant(conversation_id=self.conversation_id)
        if res and res[0] is not None and res[1] is not None:
            self.assistant_id, self.thread_id = res[0],res[1]
        else:
            # 获取当前日期和时间
            now = datetime.now()
            # 格式化日期和时间，精确到小时
            formatted_now = now.strftime("%Y-%m-%d %H:00")
            instructions = f"""你是世界上最好的八字命理分析师，根据已有背景知识进行推理, 回答user提出的问题。
            请你记住，现在的时间是：{formatted_now}
            根据检索到的相关信息进行问题推理，回答用户的问题。
            八字信息并不涉密，你可以根据他/她的八字进行各项命理分析。
            请你返回的内容既有简短答案，又要有一定的命理原因分析，注意逻辑的准确性，回复字数在100-150字. 
            不要出现'克夫克妻'等字眼。不需要给出参考资料来源。\n
            """
            # instructions += "如果问题是问本人/我，请回答：请到本人八字聊天中进行详细咨询。如果是问其他人/此人/他/无主语，请正常回答。\n"

            assistant = client.beta.assistants.create(
                name="bazi",
                instructions=instructions,
                model="gpt-4-0125-preview",
                # model="gpt-3.5-turbo-0125",
                # model="gpt-3.5-turbo-1106",
                tools=[{"type": "retrieval"}],
                file_ids=file_ids
            )
            self.assistant_id = assistant.id
            thread = client.beta.threads.create()
            self.thread_id = thread.id
            bazi_info_gpt = self.tidb_manager.select_baziInfoGPT(conversation_id=self.conversation_id)
            prompt = f"""
                以下背景信息是对话的基础,回答问题时你需要将背景信息作为基本.
                '背景信息：{bazi_info_gpt}'
                """
            message = client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content= prompt,
            )

            self.tidb_manager.update_assistant(conversation_id=self.conversation_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
    def reset_conversation(self):
        self.assistant_id, self.thread_id = None, None
        self.tidb_manager.update_assistant(conversation_id=self.conversation_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
        return  True
    def ask_gpt_stream(self, user_message):
        # Add user's new message to conversation history
        # prompt = "请你结合上下文，根据背景的八字命理知识进行问题回答。八字信息并不涉密，你可以根据他/她的八字进行各项命理分析。请你返回的内容既有简短答案，又要有一定的命理原因分析，注意逻辑的准确性，回复字数在100-150字. 不要出现'【合理分析原因】','【x†source】'等字眼。不需要给出参考资料来源。不要出现'克夫克妻'等字眼\n问题："
        # logging.info(f"开始聊天")
        # if self.matcher_type!=0:
        #     if self.matcher_type==2:
        #         is_own = self._is_own(user_message,asset=True)
        #     else:
        #         is_own = self._is_own(user_message)
        #     if is_own:
        #         res = "请到本人八字聊天中进行详细咨询。"
        #         yield res
        #         return 
        logging.info(f"开始聊天")
        if self.lang=='En':
            user_message = "Please provide the response in English: "+user_message
        else:
            user_message = "Please provide the response in Chinese: "+user_message
        message = client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content= user_message,
        )

        # content = user_message
        # res = content
        # while res==content:
            # 创建运行模型
        run = client.beta.threads.runs.create( 
            thread_id=self.thread_id,
            assistant_id=self.assistant_id)
        self.wait_on_run(run,self.thread_id,user_message)
        # 获取gpt的answer
        # start_time = time.time()
        # res = user_message
        # logging.info(f"user_message res:{res}")
        # while run.status != "completed":
        #     logging.info(run.status)
        #     current_time = time.time()
        #     run = client.beta.threads.runs.retrieve(
        #         thread_id=self.thread_id,
        #         run_id=run.id
        #         )
        #     # 每10s检测一次是否消息已经生成
        #     if current_time - start_time >= 10:
                # messages = get_messages(self.thread_id)
                # if len(messages['data'][0]['content'])>0:
                #     res = messages['data'][0]['content'][0]['text']['value']
                #     if res != user_message:
                #         # 取消当前请求
                #         # cancel_run(thread_id,run_id)
                #         break
        #         start_time = time.time()
        #     time.sleep(1)
        # logging.info(f"out while res:{res}")
    # if res == user_message:
        messages = client.beta.threads.messages.list(thread_id=self.thread_id)
        res = messages.data[0].content[0].text.value
        res = self.remove_brackets_content(res)
        logging.info(f"final res:{res}")
        yield res
    def remove_brackets_content(self,sentence):
        import re
        # 使用正则表达式匹配"【】"及其内部的内容，并将其替换为空
        new_sentence = re.sub(r'【.*?】', '', sentence)
        return new_sentence
    
    def wait_on_run(slef, run, thread_id,message=None):
        while run.status == "queued" or run.status == "in_progress":
            try:
                # messages = get_messages(self.thread_id)
                messages = client.beta.threads.messages.list(thread_id=self.thread_id)
                # if len(messages['data'][0]['content'])>0:
                if len(messages.data[0].content)>0:
                    res = messages.data[0].content[0].text.value
                    logging.info(f"now the message is :{res}")
                    if res != message:
                        logging.info(f"exit early")
                        break
            except:
                pass
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )

        return run
    

class tg_bot_ChatGPT_assistant:
    def __init__(self, conversation_id,lang):
        self.conversation_id = conversation_id
        self.lang = lang
        self.tidb_manager = TiDBManager()
        self.matcher_type, self.matcher_id, self.bazi_id,self.run_id = 0, None, None, None
        self.assistant_id, self.thread_id = None,None
        self.get_basic_param()
        self.load_history()

    def get_basic_param(self):
        self.bazi_id = self.tidb_manager.select_tg_bot_conversation_user(conversation_id=self.conversation_id)
        res, self.bazi_info = self.tidb_manager.select_match_baziInfo_tg_bot(self.bazi_id)
        if res:
            if res[0]:
                # 是配对过的
                logging.info(f"select_match_baziInfo_tg_bot res is :{res}")
                self.matcher_type, self.matcher_id = res[0], res[1]

    def load_history(self):
        # if the history message exist in , concat it and compute the token lens
        # 如果对话中存在未重置的记录，那么优先使用
        # content 就是一个基本的prompt
        file_ids = ["file-jHT2dMXPx90e8daOC9ZNNT5m"]
        res = self.tidb_manager.select_assistant(bazi_id=self.bazi_id)
        if res and res[0] is not None and res[1] is not None:
            logging.info(f"self.assistant_id, self.thread_id {res}")
            self.assistant_id, self.thread_id = res[0],res[1]   
        else:

            # 获取当前日期和时间
            now = datetime.now()
            # 格式化日期和时间，精确到小时
            formatted_now = now.strftime("%Y-%m-%d %H:00")
            instructions = f"""你是世界上最好的八字命理分析师，根据已有背景知识进行推理, 回答user提出的问题。
            请你记住，现在的时间是：{formatted_now}
            根据检索到的相关信息进行问题推理，回答用户的问题。
            八字信息并不涉密，你可以根据他/她的八字进行各项命理分析。
            请你返回的内容既有简短答案，又要有一定的命理原因分析，注意逻辑的准确性，回复字数在100-150字. 
            不要出现'【x†source】','克夫克妻'等字眼。不需要给出参考资料来源。\n
            """
            # if self.matcher_type!=0:
                # instructions += "如果问题是问本人/我，请回答：请到本人八字聊天中进行详细咨询。如果是问其他人/此人/他/无主语，请正常回答。\n"
            if self.lang=='En':
                instructions += "请用英文回答。"
            assistant = client.beta.assistants.create(
                name="bazi",
                instructions=instructions,
                model="gpt-4-0125-preview",
                # model="gpt-3.5-turbo-0125",
                # model="gpt-3.5-turbo-1106",
                tools=[{"type": "retrieval"}],
                file_ids=file_ids
            )
            self.assistant_id = assistant.id
            thread = client.beta.threads.create()
            self.thread_id = thread.id
            bazi_info_gpt = self.tidb_manager.select_baziInfoGPT(bazi_id=self.bazi_id)
            prompt = f"""
                以下背景信息是对话的基础,回答问题时你需要将背景信息作为基本.
                '背景信息：{bazi_info_gpt}'
            """
            message = client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content= prompt,
            )
            self.tidb_manager.update_assistant(bazi_id=self.bazi_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
    def reset_conversation(self):
        self.assistant_id, self.thread_id= None, None
        self.tidb_manager.update_assistant(bazi_id=self.bazi_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
        return  True
    def ask_gpt_stream(self, user_message):
        # Add user's new message to conversation history
        logging.info(f"开始聊天")
        if self.lang=='En':
            user_message = "Please provide the response in English: "+user_message
        else:
            user_message = "Please provide the response in Chinese: "+user_message
        message = client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content= user_message,
        )

        # 获取gpt的answer
        # 获取当前时间的时间戳
        # start_time = time.time()
        # res = user_message
        # logging.info(f"user_message res: {res}")
        # while run.status != "completed":
        #     logging.info(run.status)
        #     current_time = time.time()
        #     run = client.beta.threads.runs.retrieve(
        #         thread_id=self.thread_id,
        #         run_id=run.id
        #         )
        #     # 每10s检测一次是否消息已经生成
        #     if current_time - start_time >= 10:
                # messages = get_messages(self.thread_id)
                # if len(messages['data'][0]['content'])>0:
                #     res = messages['data'][0]['content'][0]['text']['value']
                #     if res != user_message :
                #         # 取消当前请求
                #         # cancel_run(thread_id,run_id)
                #         break
        #         start_time = time.time()
        #     time.sleep(1)
        # logging.info(f"out while res:{res}")
        # if res == user_message:
                # 创建运行模型
        run = client.beta.threads.runs.create( 
            thread_id=self.thread_id,
            assistant_id=self.assistant_id)
        self.run_id = run.id
        self.wait_on_run(run,self.thread_id,user_message)
        messages = client.beta.threads.messages.list(thread_id=self.thread_id)
        res = messages.data[0].content[0].text.value
        res = self.remove_brackets_content(res)
        logging.info(f"final res:{res}")
        yield res
    def remove_brackets_content(self,sentence):
        import re
        # 使用正则表达式匹配"【】"及其内部的内容，并将其替换为空
        new_sentence = re.sub(r'【.*?】', '', sentence)
        return new_sentence
    def wait_on_run(slef, run, thread_id,message=None):
        while run.status == "queued" or run.status == "in_progress":
            try:
                messages = get_messages(self.thread_id)
                if len(messages['data'][0]['content'])>0:
                    res = messages['data'][0]['content'][0]['text']['value']
                    logging.info(f"now the message is :{res}")
                    if res != message:
                        logging.info(f"exit early")
                        break
            except:
                pass
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )

        return run
        
class options:
    def __init__(self,year,month,day,time,b=False,g=True,r=False,n=False):
        self.year = year
        self.month = month
        self.day = day
        self.time = time
        self.b = b
        self.g = g
        self.r = r
        self.n = n

def stream_output(message=None, user_id=None,bazi_info=None):
    # Stream的格式：<chunk>xxxxx</chunk><chunk>{id:'xxxx'}</chunk>
    # streams = ["<chunk>", bazi_info, "</chunk>","<chunk>",f"{{'user_id':{user_id}}}","</chunk>"]
    if message:
        yield f"{message}"
    logging.info(message)
    if bazi_info:
        yield bazi_info
        # answer = ""
    if user_id:
        user_data = {'user_id':user_id}
        json_user_data = json.dumps(user_data)
        yield f"<chunk>{json_user_data}</chunk>"
def get_coin_data(name):
    try:
        tidb_manager = TiDBManager()
        res = tidb_manager.select_coin_id(name = name)
        import requests
        base_url = 'https://pro-api.coinmarketcap.com'
        # Endpoint for getting cryptocurrency quotes
        endpoint = '/v2/cryptocurrency/quotes/latest'
        # Parameters
        params = {
            'id': str(res),  # Replace with the actual ID you want to query
        }

        # Headers
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': os.environ["CMC_API_KEY"],
        }

        # Make the request
        response = requests.get(base_url + endpoint, headers=headers, params=params)
        data = response.json()
        # print(data)
        coin_data = data['data'][str(res)]
        return coin_data
    except:
        return None
def get_messages(thread_id):
    import http.client
    import json
    conn = http.client.HTTPSConnection("api.openai.com")
    payload = ''
    headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'OpenAI-Beta': 'assistants=v1',
    'Authorization': 'Bearer '+os.environ["OPENAI_API_KEY"]
    }
    conn.request("GET", "/v1/threads/"+thread_id+"/messages", payload, headers)
    res = conn.getresponse()
    data = res.read()
    result = json.loads(data)
    return result

def cancel_run(thread_id,run_id):
    import http.client

    conn = http.client.HTTPSConnection("api.openai.com")
    payload = ''
    headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'OpenAI-Beta': 'assistants=v1',
    'Authorization': 'Bearer '+os.environ["OPENAI_API_KEY"]
    }
    conn.request("POST", "/v1/threads/"+thread_id+"/runs/"+run_id+"/cancel", payload, headers)
    res = conn.getresponse()
    data = res.read()
    logging.info(f"cancel run:{data.decode('utf-8')}")

def translate(text):
    GOOGLE_TRANSLATE_URL = 'http://translate.google.com/m?q=%s&tl=%s&sl=%s'
    text = parse.quote(text)
    url = GOOGLE_TRANSLATE_URL % (text,"en","zh-CN")
    response = requests.get(url)
    data = response.text
    expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
    result = re.findall(expr, data)
    if (len(result) == 0):
        res = None
    else:
        res = html.unescape(result[0])
    return res

def rec_question(bazi_info_gpt,user_message,lang=None):
    if lang=="En":
        system_prompt = f""""
    You are a master at asking questions. Below are some background knowledge and sample questions on the Eight Characteristics, which require you to generate three more Eight Character Numerology questions related to the background knowledge and sample questions.
    Background knowledge:
    {bazi_info_gpt}

    Sample question.
    {user_message}    
    """
        user_prompt = f"""Give me three relevant questions, note that the subject is the same as the subject of the question, and also give me questions that don't include my love life or significant other. Return as json, e.g. {{"response": list of three related questions}}"""
    else:
        system_prompt = f"""
        你是提问题的高手，下面是一些八字的背景知识和问题示例,需要你再生成和背景知识及问题示例相关的三个八字命理问题。
        背景知识：
        {bazi_info_gpt}

        问题示例:
        {user_message}    
        """
        user_prompt = f"""给我三个相关问题，注意主语与问题的主语一致，另外给我的问题不要包含感情生活和另一半。以json的形式返回, 如{{"response":三个相关问题的list}}"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
        messages=[{"role": "system", "content": system_prompt},
                {"role": "user", "content":user_prompt}],
        max_tokens = 1024,
        temperature = 0,
        response_format={"type": "json_object"}

    )
    string_res = completion.choices[0].message.content.strip()
    string_res = json.loads(string_res)
    return string_res["response"]

@app.route('/api/baziAnalysis',methods=['POST','GET'])
def baziAnalysis_stream():
    year = '2000'
    month = '5'
    day = '5'
    time = '8'
    g = True
    b = False
    n = False
    r = False

    if request.method =="POST":
        logging.info(f"baziAnalysis POST_data: {request.get_json()}") 
        year = request.get_json().get("year")
        month = request.get_json().get("month")
        day = request.get_json().get("day")
        time = request.get_json().get("time")
        name = request.get_json().get("name")
        # lang = data.get("lang")
        lang = request.headers.get('Lang')

        try:
            year = int(year)
            month = int(month)
            day = int(day)
        except:
            return jsonify({"error":"无效的数据格式"}, 400)
        conversation_id = request.get_json().get("conversation_id")
        n = request.get_json().get("n")
        if int(time.split("-")[0])>=23:
            time = 0
        else:
            time = int(int(time.split("-")[0])/2  + int(time.split("-")[1]) / 2 ) # 提取开始小时
        op = options(year=year,month=month,day=day,time=time,g=g,b=b,n=n,r=r)
        (mingyun_analysis,chushen_analysis),bazi_info_gpt = bazipaipan(year,month,day,time,n,name=name)
        bazi_info = baziAnalysis(op,mingyun_analysis,chushen_analysis)
        user_id = str(uuid.uuid4())
        tidb_manager = TiDBManager()
        birthday = datetime(year, month, day, time)
        first_reply = "您好，欢迎使用AI算命。\n" + bazi_info_gpt.split("---------------")[0]
        tidb_manager.insert_baziInfo(user_id, birthday, bazi_info, bazi_info_gpt, conversation_id,first_reply=first_reply)
        # 如果需要翻译成英文
        if lang=='En':
            result_text = translate(first_reply)
        else:
            result_text = first_reply
        return Response(stream_output(None,user_id,result_text), mimetype="text/event-stream")

    if request.method == "GET":
        date_str = request.args.get('date', '')
        g = request.args.get('g', True)
        b = request.args.get('b', False)
        n = request.args.get('n', False)
        r = request.args.get('r', False)
        try:
            year, month, day, time = map(str, date_str.split('-'))
            if g!=True:
                g = False
            # date_time = datetime(year, month, day, hour)
            print(year, month, day, time,g,b,n,r)
        except ValueError:
            return jsonify({"error":"无效的日期格式。请使用 YYYY-M-D-H 格式。"}, 400)
        op = options(year=year,month=month,day=day,time=time,g=g,b=b,n=n,r=r)
        output = baziAnalysis(op)
        return Response((output,user_id), content_type="text/plain; charset=utf-8")


@app.route('/api/baziMatch',methods=['POST','GET'])
def baziMatchRes():
    if request.method =="POST":
        tidb_manager = TiDBManager()
        data = request.get_json()
        logging.info(f"data is :{data}")
        year,month,day,t_ime,user_id,n = data['year'], data['month'], data['day'], data['time'], data['user_id'], data['n']
        name = data.get("name")
        matcher_type = data["matcher_type"]
        lang = request.headers.get('Lang')
        try:
            year = int(year)
            month = int(month)
            day = int(day)
        except:
            return jsonify({"error":"无效的数据格式"}, 400)
        conversation_id = request.get_json().get("conversation_id")
        if int(t_ime.split("-")[0])>=23:
            t_ime = 0
        else:
            t_ime = int(int(t_ime.split("-")[0])/2  + int(t_ime.split("-")[1]) / 2 ) # 提取开始小时
        birthday = tidb_manager.select_birthday(user_id)
        birthday_match = datetime(year, month, day, t_ime)

        if matcher_type==1: # 与他人匹配
            match_res = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime)
            op = options(year=year,month=month,day=day,time=t_ime,n=n)
            gender = n
            (mingyun_analysis,chushen_analysis),res_gpt = bazipaipan(year,month,day,t_ime,gender,name)
            res = baziAnalysis(op,mingyun_analysis,chushen_analysis)
            head = "他人/配对者/配对人 的八字背景信息如下:\n"
            db_res = head + res + "\n" + match_res
            logging.info(f"res is:{res}")
            db_res_gpt = head + res_gpt + "\n" + match_res
            first_reply = "您好，欢迎使用AI算命。\n" + res_gpt.split("---------------")[0]
            tidb_manager.insert_baziInfo(user_id, birthday, db_res, db_res_gpt, conversation_id, birthday_match=birthday_match,first_reply=first_reply)
            # 如果需要翻译成英文
            if lang=="En":
                result_text = translate(first_reply)
            else:
                result_text = first_reply
            return Response(stream_output(None, None,result_text), mimetype="text/event-stream")

        else:
            name = data["name"]
            coin_data = get_coin_data(name)
            logging.info(f"coin data is {coin_data}")
            res = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime,name=name,coin_data=coin_data)
            db_res_gpt = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime,name=name,coin_data=coin_data,own=True)

            logging.info(f"res is:{res}")
            tidb_manager.insert_baziInfo(user_id, birthday, res, db_res_gpt, conversation_id, birthday_match=birthday_match,first_reply=db_res_gpt)
            return Response(stream_output(res, None), mimetype="text/event-stream")

@app.route('/api/get_bazi_info', methods=['POST'])
def get_bazi_info():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    tidb_manager = TiDBManager()
    bazi_info = tidb_manager.select_baziInfo(conversation_id=conversation_id)
    # Initialize or retrieve existing ChatGPT instance for the user
    return Response(stream_output(bazi_info,), mimetype="text/event-stream")

@app.route('/api/chat_bazi', methods=['POST'])
def chat_bazi():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    lang = request.headers.get('Lang')
    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT_assistant(conversation_id, lang=lang, matcher_type=0)
    logging.info(f"conversation_id {conversation_id}, message {user_message}")
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@app.route('/api/chat_bazi_match', methods=['POST'])
def chat_bazi_match():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    matcher_type = data.get('matcher_type')
    lang = request.headers.get('Lang')
    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT_assistant(conversation_id, lang=lang, match=True, matcher_type=matcher_type)
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@app.route('/api/reset_chat', methods=['POST'])
def reset_chat():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    matcher_id = data.get('matcher_id')

    chat = ChatGPT_assistant(conversation_id)
    res = chat.reset_conversation()
    # Return the ChatGPT's response
    if res:
        return jsonify({"status": "success"}, 200)
    else:
        return jsonify({"status": f"database reset Error, where conversation_id={conversation_id}"}, 500)


@app.route('/api/assets_insert', methods=['POST'])
def asset_insert():
    data = request.get_json()
    name = data.get('name')
    birthday = data.get('birthday')
    user_id = data.get('user_id')
    is_public = data.get('is_public')
    tidb_manager = TiDBManager()
    # 如果是公共的财产时间，则不用记录user_id
    if is_public == True:
        res = tidb_manager.insert_asset(name,birthday)
    # 如果是用户单独导入的财产，记录user_id
    else:
        res = tidb_manager.insert_asset(name,birthday,user_id)
    # Return the ChatGPT's response
    if res:
        return jsonify({"status": "success"}, 200)
    else:
        return jsonify({"status": "database insert Error"}, 500)

@app.route('/api/assets_select', methods=['POST'])
def asset_select():
    data = request.get_json()
    user_id = data.get('user_id')
    tidb_manager = TiDBManager()
    _res = tidb_manager.select_asset(user_id)
    # res = res_
    res = [(name, birthday) for name, birthday, _ in _res]
    # res = tidb_manager.select_asset(user_id)
    # Return the ChatGPT's response
    if res:
        return jsonify({"status": "success", "data":res}, 200)
    else:
        return jsonify({"status": "database select Error"}, 500)
@app.route('/api/question_rec', methods=['POST'])
def question_rec():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    matcher_type = data.get('matcher_type')
    lang = request.headers.get('Lang')
    # 获取精确批文 和 thread_id
    tidb_manager = TiDBManager()
    bazi_info = tidb_manager.select_baziInfo(conversation_id=conversation_id)
    # 如果user_message存在。 说明非首次回复
    if lang=="En":
        bazi_info = translate(bazi_info)
    if user_message:
        result = rec_question(bazi_info, user_message)
    else:
        if matcher_type==1:
            if lang=="En":
                questions = [
                "What is the personality like?",
                "Are we suitable to start a business together?",
                "How is the financial fortune?",
                "How to make up for the lack of fire in the five elements?",
                "When can getting married be expected?",
                "What kind of job is right?",
                "What is the lucky number?",
                "When will a romantic phase occur?",
                "Any suggestions for improving Feng Shui and the Five Elements?"
                ]
            else:
                questions = [
                "此人性格怎样？",
                "我和这个人适合合作创业吗？",
                "此人财运怎么样？",
                "五行缺火该怎么补？",
                "什么时候能结婚？",
                "什么样的工作适合这个人？",
                "幸运数字是什么？",
                "什么时候走桃花运？",
                "有什么改善风水和五行的建议？"
                ]
        elif matcher_type==2:
            pass
        else:
            if lang=="En":
                questions = [
                "How is my financial fortune?",
                "When can I get married?",
                "What kind of job is right for me?",
                "How to make up for the lack of fire in the five elements?",
                "What's my lucky number?",
                "When can I have a girlfriend？",
                "Any suggestions for improving Feng Shui and the Five Elements?"
                ]
            else:
                questions = [
                "我的财运怎么样？",
                "我什么时候能结婚？",
                "什么样的工作适合我？",
                "五行缺火该怎么补？",
                "我的幸运数字是什么？",
                "我什么时候走桃花运？",
                "有什么改善风水和五行的建议？"]

        # 从问题库中随机给出
        result = ["今年运势怎么样？","什么时候适合结婚？","幸运数字是多少？"]
    if result:
        return jsonify({"status": "success", "data":result}, 200)
    else:
        return jsonify({"status": "database select Error"}, 500)
@app.route('/api/tg_bot/first_visit',methods=['POST'])
def tg_bot_first_visit():
    if request.method =="POST":
        data = request.get_json()
        conversation_id = data['conversation_id']
        tidb_manager = TiDBManager()
        res = tidb_manager.select_tg_bot_conversation_user(conversation_id)
        if res:
            return jsonify({"status": "success, not first time.", "data": 0,"status_code":200})
        else:
            return jsonify({"status": "error, it is first time.", "data": 1,"status_code":200})

@app.route('/api/tg_bot/get_matcher',methods=['POST'])
def tg_bot_get_matcher():
    if request.method =="POST":
        data = request.get_json()
        user_id = data['user_id']
        matcher_type = data['matcher_type']
        tidb_manager = TiDBManager()
        if matcher_type==1:
            res = tidb_manager.select_other_human(user_id)
        elif matcher_type==2:
            _res = tidb_manager.select_asset(user_id)
            res = [(name, id) for name, _, id in _res]
        else:
            response = jsonify({"status": "matcher_type Error"})
            response.status_code = 500
        if res:
            response = jsonify({"status": "success","data":res})
            response.status_code = 200
        else:
            response = jsonify({"status": "success","data":[]})
            response.status_code = 200
        return response

@app.route('/api/tg_bot/chat', methods=['POST'])
def tg_bot_chat():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    lang = data.get('lang')
    chat = tg_bot_ChatGPT_assistant(conversation_id,lang)
    # Initialize or retrieve existing ChatGPT instance for the user
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")


@app.route('/api/tg_bot/bazi_insert', methods=['POST'])
def tg_bot_bazi_insert():
    data = request.get_json()
    birthday = data.get('birthday') # 格式：2000-5-5-10
    conversation_id = data.get('conversation_id')
    matcher_type = data.get('matcher_type')
    gender = data.get("gender")
    name = data.get("name")
    # name_or_gender = data.get('name_or_gender') # gender:true代表女 false代表男 name直接输入名字
    user_id = data.get('user_id')
    matcher_id = data.get('matcher_id')
    lang = data.get('lang')

    tidb_manager = TiDBManager()
    # 如果matcher_type 是0代表本人，是1，代表其他人， 2代表资产(int)
    if matcher_type == 0:
        # 插入自己八字
        n = gender
        year, month, day, time = map(int, birthday.split('-'))
        op = options(year=year,month=month,day=day,time=time,n=n)
        # bazi_info = baziAnalysis(op)
        birthday = datetime(year, month, day, time)
        bazi_id = tidb_manager.select_bazi_id(user_id=user_id)

        # bazi_info_gpt = bazipaipan(year,month,day,time,n)
        (mingyun_analysis,chushen_analysis),bazi_info_gpt = bazipaipan(year,month,day,time,n,name=name,tg_bot=True)
        bazi_info = baziAnalysis(op,mingyun_analysis,chushen_analysis)
        first_reply = "您好，欢迎使用AI算命。\n" + bazi_info_gpt.split("---------------")[0]

        user_id = user_id
        tidb_manager = TiDBManager()
        if bazi_id:
            tidb_manager.update_bazi_info(birthday=birthday, bazi_info=bazi_info, bazi_info_gpt=bazi_info_gpt,bazi_id=bazi_id,first_reply=first_reply)
        else:
            bazi_id = tidb_manager.insert_baziInfo(user_id, birthday, bazi_info, bazi_info_gpt, conversation_id,first_reply=first_reply)
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
        # 如果需要翻译成英文
        if lang=="En":
            result_text = translate(first_reply)
        else:
            result_text = first_reply
        return Response(stream_output(None,user_id,result_text), mimetype="text/event-stream")

    elif matcher_type == 1:
        birthday_user = tidb_manager.select_birthday(user_id)
        logging.info(f"res is:{birthday_user}")
        n = gender
        year_match, month_match, day_match, time_match = map(int, birthday.split('-'))
        if matcher_id:
            birthday_match = tidb_manager.select_birthday(matcher_type=1,matcher_id=matcher_id)
            year_match,month_match,day_match,time_match = birthday_match.year,birthday_match.month,birthday_match.day,birthday_match.hour
        else:
            birthday_match = datetime(year_match, month_match, day_match, time_match)
            matcher_id = tidb_manager.insert_other_human(n, birthday_match, user_id,name=name)
        res_match = baziMatch(birthday_user.year,birthday_user.month,birthday_user.day,birthday_user.hour, year_match,month_match,day_match,time_match)
        op = options(year=year_match,month=month_match,day=day_match,time=time_match,n=n)
        (mingyun_analysis,chushen_analysis),res_gpt = bazipaipan(year_match,month_match,day_match,time_match,gender,name=name,tg_bot=True)
        res = baziAnalysis(op,mingyun_analysis,chushen_analysis)
        head = "他人/配对者/配对人 的八字背景信息如下:\n"
        db_res = head + res + "\n" + res_match
        logging.info(f"res is:{res}")
        db_res_gpt = head + res_gpt + "\n" + res_match
        first_reply = "您好，欢迎使用AI算命。\n" + res_gpt.split("---------------")[0]
        bazi_id = tidb_manager.insert_baziInfo(user_id, birthday_user, db_res, db_res_gpt, conversation_id, birthday_match=birthday_match,matcher_type=matcher_type, matcher_id=matcher_id,first_reply=first_reply)
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)

        # 如果需要翻译成英文
        if lang=="En":
            result_text = translate(first_reply)
        else:
            result_text = first_reply
        return Response(stream_output(None, None,result_text), mimetype="text/event-stream")

    elif matcher_type==2: # 配对资产
        birthday_user = tidb_manager.select_birthday(user_id)
        year_match, month_match, day_match, time_match = map(int, birthday.split('-'))
        if matcher_id:
            birthday_match = tidb_manager.select_birthday(matcher_type=2,matcher_id=matcher_id)
            year_match,month_match,day_match,time_match = birthday_match.year,birthday_match.month,birthday_match.day,birthday_match.hour
        else:
            birthday_match = datetime(year_match, month_match, day_match, time_match)
            matcher_id = tidb_manager.insert_asset(name, birthday_match,user_id=user_id)
        res = baziMatch(birthday_user.year,birthday_user.month,birthday_user.day,birthday_user.hour, year_match,month_match,day_match,time_match,name=name)
        logging.info(f"res is:{res}")
        bazi_id = tidb_manager.insert_baziInfo(user_id, birthday_user,res, res, conversation_id, birthday_match=birthday_match, matcher_type=matcher_type, matcher_id=matcher_id,first_reply=res)
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)

        # 如果需要翻译成英文
        if lang=="En":
            result_text = translate(res)
        else:
            result_text = res
        return Response(stream_output(None, None, result_text), mimetype="text/event-stream")
    else:
        return jsonify({"status": f"POST data param type error! matcher type is number! where conversation_id={conversation_id}"}, 500)

@app.route('/api/tg_bot/reset_chat',methods=['POST'])
def tg_bot_bazi_info():
    '''
    传入conversation_id, birthday, n。如果conversation_id存在，那么对应的输入生日就是新增八字配对。如果不存在那就是给用户算八字。如果没有生日就是重置对话。
    '''
    if request.method =="POST":
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')
        matcher_id = data.get('matcher_id')
        matcher_type = data.get('matcher_type')
        name = data.get("name")
        lang = data.get("lang")
        tidb_manager = TiDBManager()
        # 重置当前对话，并获取八字背景信息；重置
        if matcher_type==0: # 获取自己的八字， match
            bazi_info = tidb_manager.select_first_reply(user_id=user_id)
            bazi_id = tidb_manager.select_bazi_id(user_id=user_id)
        # 重置当前对话 其他人
        else:
            bazi_info = tidb_manager.select_first_reply(matcher_id=matcher_id)
            bazi_id = tidb_manager.select_bazi_id(matcher_id=matcher_id)
            logging.info(f"bazi_id is {bazi_id}")
        if matcher_type==2:
            if bazi_info ==False or bazi_id ==False:
                birthday_match = tidb_manager.select_birthday(matcher_type=2,matcher_id=matcher_id)
                year_match,month_match,day_match,time_match = birthday_match.year,birthday_match.month,birthday_match.day,birthday_match.hour
                birthday_user = tidb_manager.select_birthday(user_id)
                res = baziMatch(birthday_user.year,birthday_user.month,birthday_user.day,birthday_user.hour, year_match,month_match,day_match,time_match,name=name)
                bazi_id = tidb_manager.insert_baziInfo(user_id, birthday_user,res, res, conversation_id, birthday_match=birthday_match, matcher_type=matcher_type, matcher_id=matcher_id,first_reply=res)
                tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
                return Response(stream_output(None, None, res), mimetype="text/event-stream")
        # chat = tg_bot_ChatGPT_assistant(conversation_id)
        # res = chat.reset_conversation()
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
        # 如果需要翻译成英文
        if lang=="En":
            result_text = translate(bazi_info)
        else:
            result_text = bazi_info
        return Response(stream_output(None, None, result_text), mimetype="text/event-stream")

@app.route('/api/translate',methods=['POST'])
def translate_():
    request_data = request.get_json()
    text = request_data.get('text')
    res = translate(text)
    if res:
        return Response(stream_output(None, None, res), mimetype="text/event-stream")
    else:
        return jsonify({"status": f"google translate error!"}, 500)
@app.route('/test')
def test():
    return jsonify({"res":"test!"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
