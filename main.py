import openai
import json
import os
import time
from flask import Flask, Response, request, stream_with_context, jsonify
from flask_cors import CORS
import os
import requests
import random
import openai
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
logging.basicConfig(filename='AI_fortune.log', level=logging.DEBUG, encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
# 跨域支持
CORS(app, resources=r'/*')

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

    def insert_other_human(self, gender, birthday, user_id):
        # try:
        generated_uuid = str(uuid.uuid4())
        with self.db.cursor() as cursor:
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
            sql = "SELECT gender, birthday, id FROM AI_fortune_tg_bot_other_human WHERE user_id=%s"
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
    def insert_baziInfo(self, user_id, birthday, bazi_info, conversation_id, birthday_match=None, matcher_type=None, matcher_id=None):
        generated_uuid = str(uuid.uuid4())
        logging.info(f"insert_baziInfo{user_id, birthday, conversation_id}")
        with self.db.cursor() as cursor:
            if birthday_match:
                if matcher_type: # matcher_type 代表是tg_bot
                    sql = """
                        INSERT INTO AI_fortune_bazi (id, user_id, birthday, birthday_match, bazi_info,conversation_id,matcher_type,matcher_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), birthday_match = VALUES(birthday_match), bazi_info = VALUES(bazi_info)
                        """
                    cursor.execute(sql, (generated_uuid, user_id, birthday, birthday_match, bazi_info, conversation_id, matcher_type, matcher_id))
                else:    
                    sql = """
                        INSERT INTO AI_fortune_bazi (id, user_id, birthday, birthday_match, bazi_info,conversation_id) VALUES (%s, %s, %s, %s, %s, %s)
                        """
                    cursor.execute(sql, (generated_uuid, user_id, birthday, birthday_match, bazi_info, conversation_id))
            else:
                sql = """
                    INSERT INTO AI_fortune_bazi (id, user_id, birthday, bazi_info, conversation_id) VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), bazi_info = VALUES(bazi_info)
                    """
                cursor.execute(sql, (generated_uuid, user_id, birthday, bazi_info, conversation_id))
        self.db.commit()
        return generated_uuid

    def update_bazi_info(self, birthday, bazi_info, bazi_id):
        with self.db.cursor() as cursor:
            sql = """
                UPDATE AI_fortune_bazi SET birthday = %s, bazi_info = %s WHERE id = %s 
                """
            cursor.execute(sql, (birthday, bazi_info, bazi_id))
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

class ChatGPT:
    def __init__(self, conversation_id, match=None):
        self.conversation_id = conversation_id
        self.messages = []
        self.tidb_manager = TiDBManager()
        self.match=match
        # self.user_id = self.tidb_manager.get_user_id(self.conversation_id)
        # get the history messages
        if match:
            self.load_match_history()
        else:
            self.load_history()  # Load the conversation history

    def _num_tokens_from_string(self, string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        tokens=encoding.encode(string)
        return len(tokens)
    def _trim_conversations(self, bazi_info, conversation_messages, max_tokens=16000):
        # add the bazi_info as background in index 0
        conversation_messages.insert(0,bazi_info)
        total_tokens = sum(self._num_tokens_from_string(str(message)) for message in conversation_messages)
        # if total tokens exceeds the max_tokens, delete the oldest message
        # 如果总token数超过限制，则删除旧消息 
        logging.info(f"The number of summary is: {total_tokens}")
        while total_tokens > max_tokens:
            # delete the first list item 删除列表的第一个元素
            removed_message = conversation_messages.pop(0)  
            # update total tokens 更新总token数
            total_tokens -= self._num_tokens_from_string(removed_message) 
        return conversation_messages
    def _is_own(self,message):
        messages = []
        messages.append({"role": "user", "content": f"""
        你是一个语言专家，我会给你一个语句，请你告诉我这个句子 是指的我本人还是他人 还是指的我和他人。 如果是本人，返回给我1，如果是他人返回2，如果是我和他人 返回3. 如果没有任何主语返回0
        判断一下问题询问的是本人\他人\群体 
        返回格式是json, 格式如下:
        {{
            "type_":"xxxxx"
        }}
        问题:{message}"""})
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=messages
        )
        logging.info(f"问题类型:{res}")
        if '1' in res:
            return True
        else:
            return False
    def load_history(self):
        # if the history message exist in , concat it and compute the token lens
        bazi_info = self.tidb_manager.select_baziInfo(conversation_id=self.conversation_id)
        # logging.info(f"bazi_info is: {bazi_info}")
        conversation_messages = self.tidb_manager.get_conversation(conversation_id=self.conversation_id)
        # 如果对话中存在未重置的记录，那么优先使用
        # content 就是一个基本的prompt
        content = f"""我想你作为一个命理占卜分析师。你的工作是根据我给定的中国传统命理占卜的生辰八字和对应的八字批文信息作为整个对话的背景知识进行问题的回答。
        注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
        你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。


        生辰八字和对应的批文：{bazi_info}
        """
        if conversation_messages:
            conversations = self._trim_conversations(content, list(conversation_messages))
            # if the first item is not a tuple, that is bazi_info
            # logging.info(f"conversation is: {conversations}")
            if type(conversations[0]) != tuple:
                self.messages = [{"role": "system", "content": content}]
                conversations = conversations[1:]
            for conversation in conversations:
                # add user message
                self.messages.append({"role": "user", "content": conversation[0]})
                # add AI message
                self.messages.append({"role": "assistant", "content": conversation[1]})
        # 如果对话中不存在未重置的记录，那么意味着直接使用bazi_info作为背景知识
        else:
            logging.info(f"the length is :{self._num_tokens_from_string(content)}")
            self.messages = [{"role": "system", "content": content}]


    def load_match_history(self):
        # if the history message exist in , concat it and compute the token lens
        bazi_info = self.tidb_manager.select_baziInfo(conversation_id=self.conversation_id)
        conversation_messages = self.tidb_manager.get_conversation(conversation_id=self.conversation_id)
        # 如果对话中存在未重置的记录，那么优先使用
        # content 就是一个基本的prompt
        content = f"""我想你作为一个命理占卜分析师。我将给你如下信息，配对者的生辰八字，还有八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
        注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
        你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。
        

        信息：{bazi_info}
        """
        if conversation_messages:
            conversations = self._trim_conversations(content, list(conversation_messages))
            # if the first item is not a tuple, that is bazi_info
            # logging.info(f"conversation is: {conversations}")
            if type(conversations[0]) != tuple:
                self.messages = [{"role": "system", "content": content}]
                conversations = conversations[1:]
            for conversation in conversations:
                # add user message
                self.messages.append({"role": "user", "content": conversation[0]})
                # add AI message
                self.messages.append({"role": "assistant", "content": conversation[1]})
        # 如果对话中不存在未重置的记录，那么意味着直接使用bazi_info作为背景知识
        else:
            self.messages = [{"role": "system", "content": content}]

    def writeToTiDB(self, human, AI):
        self.tidb_manager.insert_conversation(self.conversation_id, human, AI)

    def ask_gpt_stream(self, user_message):
        answer = ""
        # Add user's new message to conversation history
        self.messages.append({"role": "user", "content": user_message})
        # print(self.messages)
        # Send the entire conversation history to GPT
        if self.match:
            is_own = self._is_own(user_message)
            if is_own:
                res = "请到本人八字聊天中进行详细咨询。"
                yield res
                # self.messages.append({"role": "assistant", "content": res})
                # self.writeToTiDB(user_message, res)
                return 
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=self.messages,
            stream=True
        )
        # yield "<chunk>"
        for chunk in rsp:
            data = chunk["choices"][0]["delta"].get("content","")
            answer += data
            yield data
        # yield f"</chunk><chunk>{{'user_id':{self.user_id}}}</chunk>"
        # Add GPT's reply to conversation history
        self.messages.append({"role": "assistant", "content": answer})
        logging.info(f"gpt answer is: {answer}")
        self.writeToTiDB(user_message, answer)


class tg_bot_ChatGPT:
    def __init__(self, conversation_id):
        self.conversation_id = conversation_id
        self.messages = []
        self.tidb_manager = TiDBManager()
        self.mathcer_type, self.matcher_id, self.bazi_id = None, None, None
        self.get_basic_param()
        self.load_history()

    def get_basic_param(self):
        self.bazi_id = self.tidb_manager.select_tg_bot_conversation_user(conversation_id=self.conversation_id)
        res, self.bazi_info = self.tidb_manager.select_match_baziInfo_tg_bot(self.bazi_id)
        if res:
            # 是配对过的
            logging.info(f"select_match_baziInfo_tg_bot res is :{res}")
            self.mathcer_type, self.matcher_id = res[0], res[1]

    def _num_tokens_from_string(self, string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        tokens=encoding.encode(string)
        return len(tokens)
    def _trim_conversations(self, bazi_info, conversation_messages, max_tokens=16000):
        # add the bazi_info as background in index 0
        conversation_messages.insert(0,bazi_info)
        total_tokens = sum(self._num_tokens_from_string(str(message)) for message in conversation_messages)
        # if total tokens exceeds the max_tokens, delete the oldest message
        # 如果总token数超过限制，则删除旧消息 
        while total_tokens > max_tokens:
            # delete the first list item 删除列表的第一个元素
            removed_message = conversation_messages.pop(0)  
            # update total tokens 更新总token数
            total_tokens -= self._num_tokens_from_string(removed_message) 
        return conversation_messages
    def _is_own(self,message):
        messages = []
        messages.append({"role": "user", "content": f"""
        你是一个语言专家，我会给你一个语句，请你告诉我这个句子 是指的我本人还是他人 还是指的我和他人。 如果是本人，返回给我1，如果是他人返回2，如果是我和他人 返回3. 如果没有任何主语返回0
        判断一下问题询问的是本人\他人\群体 
        返回格式是json, 格式如下:
        {{
            "type_":"xxxxx"
        }}
        问题:{message}"""})
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=messages
        )
        logging.info(f"问题类型:{res}")
        if '1' in res:
            return True
        else:
            return False
    def load_history(self):
        # if the history message exist in , concat it and compute the token lens
        conversation_messages = self.tidb_manager.get_conversation(conversation_id=self.conversation_id)
        # 如果对话中存在未重置的记录，那么优先使用
        # content 就是一个基本的prompt
        content = f"""我想你作为一个命理占卜分析师。你的工作是根据我给定的中国传统命理占卜的生辰八字和对应的八字批文信息作为整个对话的背景知识进行问题的回答。
        注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
        你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。


        生辰八字和对应的批文：{self.bazi_info}
        """
        # content = f"""我想你作为一个命理占卜分析师。我将给你如下信息，配对者的生辰八字，还有八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
        # 注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
        # 你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。


        # 信息：{self.bazi_info}
        # """

        # content = f"""我想你作为一个命理占卜分析师。我将给你如下信息，配对者的生辰八字，还有八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
        # 注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
        # 你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。


        # 信息：{self.bazi_info}
        # """
        if conversation_messages:
            conversations = self._trim_conversations(content, list(conversation_messages))
            # if the first item is not a tuple, that is bazi_info
            if type(conversations[0]) != tuple:
                self.messages = [{"role": "system", "content": content}]
                conversations = conversations[1:]
            for conversation in conversations:
                # add user message
                self.messages.append({"role": "user", "content": conversation[0]})
                # add AI message
                self.messages.append({"role": "assistant", "content": conversation[1]})
        # 如果对话中不存在未重置的记录，那么意味着直接使用bazi_info作为背景知识
        else:
            self.messages = [{"role": "system", "content": content}]


    def writeToTiDB(self, human, AI):
        self.tidb_manager.insert_conversation(self.conversation_id, human, AI, self.bazi_id)

    def ask_gpt_stream(self, user_message):
        answer = ""
        # Add user's new message to conversation history
        self.messages.append({"role": "user", "content": user_message})
        # print(self.messages)
        # Send the entire conversation history to GPT

        if self.matcher_type != 0:
            is_own = self._is_own(user_message)
            if is_own:
                res = "请到本人八字聊天中进行详细咨询。"
                yield res
                # self.messages.append({"role": "assistant", "content": res})
                # self.writeToTiDB(user_message, res)
                return 
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=self.messages,
            stream=True
        )
        # yield "<chunk>"
        for chunk in rsp:
            data = chunk["choices"][0]["delta"].get("content","")
            answer += data
            yield data
        # yield f"</chunk><chunk>{{'user_id':{self.user_id}}}</chunk>"
        # Add GPT's reply to conversation history
        self.messages.append({"role": "assistant", "content": answer})
        logging.info(f"gpt answer is: {answer}")
        self.writeToTiDB(user_message, answer)

        
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

def stream_output(message, user_id=None):
    # Stream的格式：<chunk>xxxxx</chunk><chunk>{id:'xxxx'}</chunk>
    # streams = ["<chunk>", bazi_info, "</chunk>","<chunk>",f"{{'user_id':{user_id}}}","</chunk>"]
    # for data in streams:
    #     print(data)
    #     yield(data)

    if user_id:
        user_data = {'user_id':user_id}
        json_user_data = json.dumps(user_data)
        yield f"{message}<chunk>{json_user_data}</chunk>"
    else:
        yield f"{message}"

def get_coin_data(name):
    try:
        res = tidb_manager.select_coin_id(name = name)
        import requests
        base_url = 'https://pro-api.coinmarketcap.com'
        # Endpoint for getting cryptocurrency quotes
        endpoint = '/v2/cryptocurrency/quotes/latest'
        # Parameters
        params = {
            'id': res,  # Replace with the actual ID you want to query
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
        try:
            year = int(year)
            month = int(month)
            day = int(day)
        except:
            return jsonify({"error":"无效的数据格式"}, 400)
        conversation_id = request.get_json().get("conversation_id")
        n = request.get_json().get("n")
        time = int(int(time.split("-")[0])/2  + int(time.split("-")[1]) / 2 ) # 提取开始小时
        op = options(year=year,month=month,day=day,time=time,g=g,b=b,n=n,r=r)
        bazi_info = baziAnalysis(op)
        user_id = str(uuid.uuid4())
        tidb_manager = TiDBManager()
        birthday = datetime(year, month, day, time)
        tidb_manager.insert_baziInfo(user_id, birthday, bazi_info, conversation_id)
        return Response(stream_output(bazi_info,user_id), mimetype="text/event-stream")

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
        matcher_type = data["matcher_type"]
        try:
            year = int(year)
            month = int(month)
            day = int(day)
        except:
            return jsonify({"error":"无效的数据格式"}, 400)
        conversation_id = request.get_json().get("conversation_id")
        t_ime = int(int(t_ime.split("-")[0])/2  + int(t_ime.split("-")[1]) / 2 ) # 提取开始小时
        birthday = tidb_manager.select_birthday(user_id)
        if matcher_type==1: # 与他人匹配
            match_res = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime)
            op = options(year=year,month=month,day=day,time=t_ime,n=n)
            res = baziAnalysis(op)
            db_res = res + "\n" + match_res
        else:
            name = data["name"]
            coin_data = get_coin_data(name)
            res = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime,name=name,coin_data=coin_data)
            db_res = res
        logging.info(f"res is:{res}")
        birthday_match = datetime(year, month, day, t_ime)
        tidb_manager.insert_baziInfo(user_id, birthday, db_res, conversation_id, birthday_match=birthday_match)
        return Response(stream_output(res, None), mimetype="text/event-stream")


@app.route('/api/chat_bazi', methods=['POST'])
def chat_bazi():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')

    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT(conversation_id)
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@app.route('/api/chat_bazi_match', methods=['POST'])
def chat_bazi_match():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')

    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT(conversation_id, match=True)
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@app.route('/api/reset_chat', methods=['POST'])
def reset_chat():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    tidb_manager = TiDBManager()
    res = tidb_manager.reset_conversation(conversation_id)
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
    res = [(name, birthday) for name, birthday, _ in _res]
    # res = tidb_manager.select_asset(user_id)
    # Return the ChatGPT's response
    if res:
        return jsonify({"status": "success", "data":res}, 200)
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
    chat = tg_bot_ChatGPT(conversation_id)
    # Initialize or retrieve existing ChatGPT instance for the user
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")


@app.route('/api/tg_bot/bazi_insert', methods=['POST'])
def tg_bot_bazi_insert():
    data = request.get_json()
    birthday = data.get('birthday') # 格式：2000-5-5-10
    conversation_id = data.get('conversation_id')
    matcher_type = data.get('matcher_type')
    name_or_gender = data.get('name_or_gender') # gender:true代表女 false代表男 name直接输入名字
    user_id = data.get('user_id')
    matcher_id = data.get('matcher_id')

    tidb_manager = TiDBManager()
    # 如果matcher_type 是0代表本人，是1，代表其他人， 2代表资产(int)
    if matcher_type == 0:
        # 插入自己八字
        n = name_or_gender
        year, month, day, time = map(int, birthday.split('-'))
        op = options(year=year,month=month,day=day,time=time,n=n)
        bazi_info = baziAnalysis(op)
        birthday = datetime(year, month, day, time)
        bazi_id = tidb_manager.select_bazi_id(user_id=user_id)
        if bazi_id:
            tidb_manager.update_bazi_info(birthday, bazi_info, bazi_id)
        else:
            bazi_id = tidb_manager.insert_baziInfo(user_id, birthday, bazi_info, conversation_id)
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
        return Response(stream_output(bazi_info,user_id), mimetype="text/event-stream")
    elif matcher_type == 1:
        birthday_user = tidb_manager.select_birthday(user_id)
        n = name_or_gender
        year_match, month_match, day_match, time_match = map(int, birthday.split('-'))
        if matcher_id:
            birthday_match = tidb_manager.select_birthday(matcher_type=1,matcher_id=matcher_id)
            year_match,month_match,day_match,time_match = birthday_match.year,birthday_match.month,birthday_match.day,birthday_match.hour
        else:
            birthday_match = datetime(year_match, month_match, day_match, time_match)
            matcher_id = tidb_manager.insert_other_human(n, birthday_match, user_id)
        res = baziMatch(birthday_user.year,birthday_user.month,birthday_user.day,birthday_user.hour, year_match,month_match,day_match,time_match)
        logging.info(f"res is:{res}")

        bazi_id = tidb_manager.insert_baziInfo(user_id, birthday_user, res, conversation_id, birthday_match=birthday_match, matcher_type=matcher_type, matcher_id=matcher_id)
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
        return Response(stream_output(res, user_id), mimetype="text/event-stream")
    elif matcher_type==2: # 配对资产
        birthday_user = tidb_manager.select_birthday(user_id)
        name = name_or_gender
        year_match, month_match, day_match, time_match = map(int, birthday.split('-'))
        if matcher_id:
            birthday_match = tidb_manager.select_birthday(matcher_type=2,matcher_id=matcher_id)
            year_match,month_match,day_match,time_match = birthday_match.year,birthday_match.month,birthday_match.day,birthday_match.hour
        else:
            birthday_match = datetime(year_match, month_match, day_match, time_match)
            matcher_id = tidb_manager.insert_asset(name, birthday_match,user_id=user_id)
        res = baziMatch(birthday_user.year,birthday_user.month,birthday_user.day,birthday_user.hour, year_match,month_match,day_match,time_match,name=name)
        logging.info(f"res is:{res}")
        bazi_id = tidb_manager.insert_baziInfo(user_id, birthday_user, res, conversation_id, birthday_match=birthday_match, matcher_type=matcher_type, matcher_id=matcher_id)
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
        return Response(stream_output(res, user_id), mimetype="text/event-stream")
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

        tidb_manager = TiDBManager()
        # 重置当前对话，并获取八字背景信息；重置
        if matcher_type==0: # 获取自己的八字， match
            bazi_info = tidb_manager.select_baziInfo(user_id=user_id)
            bazi_id = tidb_manager.select_bazi_id(user_id=user_id)
        # 重置当前对话 其他人
        else :
            bazi_info = tidb_manager.select_baziInfo(matcher_id=matcher_id)
            bazi_id = tidb_manager.select_bazi_id(matcher_id=matcher_id)
        tidb_manager.reset_conversation(conversation_id, bazi_id)
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
        return Response(stream_output(bazi_info, user_id), mimetype="text/event-stream")



            
@app.route('/test')
def test():
    return jsonify({"res":"test!"})
    # return Response(stream_output("你的八字是....","ryen"), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    # year = '2002'
    # month = '2'
    # day = '1'
    # time = '8'
    # g = True
    # b = False
    # n = False
    # r = False
    # op = options(year=year,month=month,day=day,time=time,g=g,b=b,n=n,r=r)
    # res= baziAnalysis(op)
    # def _num_tokens_from_string(string: str) -> int:
    #     """Returns the number of tokens in a text string."""
    #     encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    #     tokens=encoding.encode(string)
    #     return len(tokens)
    # print(_num_tokens_from_string(res))
    # print(res)
    # conversation_id = "349ed47f-6983-4426-9336-12e2307a817f"
    # user_id = "4da7f06e-a8c4-43a2-9f05-53480473faf9"
    # tidb_manager = TiDBManager()
    # messages = tidb_manager.get_conversation(conversation_id)
    # birthday = tidb_manager.select_birthday(user_id)
    # print(birthday.year)
    # baziInfo = tidb_manager.select_baziInfo(user_id)
    # print(baziInfo)
    # print(type(messages))
    # print(messages)
    # print(messages.insert(0,111))
    # user_message = "我的生日是2001年5月5号12点，给出我的生辰八字。"
    # messages.append({"role": "user", "content": user_message})
    # # print(self.messages)
    # # Send the entire conversation history to GPT
    # rsp = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo-16k",
    #     messages=messages
    # )
    # answer = rsp.get("choices")[0]["message"]["content"]

    # # Add GPT's reply to conversation history
    # messages.append({"role": "assistant", "content": answer})
    # tidb_manager.insert_conversation(conversation_id, messages)