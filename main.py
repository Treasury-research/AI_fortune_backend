import openai
import sxtwl
import json
import os
import time
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
logging.basicConfig(filename='AI_fortune.log', level=logging.DEBUG, encoding='utf-8',
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
    def insert_baziInfo(self, user_id, birthday, bazi_info, bazi_info_gpt,conversation_id, birthday_match=None, matcher_type=None, matcher_id=None):
        generated_uuid = str(uuid.uuid4())
        logging.info(f"insert_baziInfo{user_id, birthday, conversation_id}")
        with self.db.cursor() as cursor:
            if birthday_match:
                if matcher_type: # matcher_type 代表是tg_bot
                    sql = """
                        INSERT INTO AI_fortune_bazi (id, user_id, birthday, birthday_match, bazi_info, bazi_info_gpt, conversation_id,matcher_type,matcher_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), birthday_match = VALUES(birthday_match), bazi_info = VALUES(bazi_info)
                        """
                    cursor.execute(sql, (generated_uuid, user_id, birthday, birthday_match, bazi_info, bazi_info_gpt, conversation_id, matcher_type, matcher_id))
                else:    
                    sql = """
                        INSERT INTO AI_fortune_bazi (id, user_id, birthday, birthday_match, bazi_info, bazi_info_gpt, conversation_id) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                    cursor.execute(sql, (generated_uuid, user_id, birthday, birthday_match, bazi_info, bazi_info_gpt, conversation_id))
            else:
                sql = """
                    INSERT INTO AI_fortune_bazi (id, user_id, birthday, bazi_info, bazi_info_gpt, conversation_id) VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE birthday = VALUES(birthday), bazi_info = VALUES(bazi_info)
                    """
                cursor.execute(sql, (generated_uuid, user_id, birthday, bazi_info, bazi_info_gpt, conversation_id))
        self.db.commit()
        return generated_uuid

    def update_assistant(self, conversation_id, bazi_id=None, assistant_id=None,thread_id=None):
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
    def select_assistant(self, conversation_id, assistant_id=None,thread_id=None):
        with self.db.cursor() as cursor:
            sql = "SELECT assistant_id,thread_id FROM AI_fortune_bazi WHERE conversation_id=%s"
            cursor.execute(sql, (conversation_id,))
            result = cursor.fetchone()
            if result:
                return result
            else:
                return False

    def update_bazi_info(self, bazi_info, bazi_id=None, birthday=None,conversation_id = None):
        with self.db.cursor() as cursor:
            if bazi_id:
                sql = """
                    UPDATE AI_fortune_bazi SET birthday = %s, bazi_info = %s WHERE id = %s 
                    """
                cursor.execute(sql, (birthday, bazi_info, bazi_id))
            elif conversation_id:
                sql = """
                    UPDATE AI_fortune_bazi SET bazi_info = %s WHERE conversation_id = %s 
                    """
                cursor.execute(sql, (bazi_info, conversation_id))
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
    def select_baziInfoGPT(self, user_id=None, conversation_id=None, matcher_id=None):
        with self.db.cursor() as cursor:
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
    def __init__(self, conversation_id, match=None, matcher_type=None):
        self.conversation_id = conversation_id
        self.assistant_id, self.thread_id = None,None
        self.tidb_manager = TiDBManager()
        self.match=match
        self.matcher_type = matcher_type
        # self.user_id = self.tidb_manager.get_user_id(self.conversation_id)
        # get the history messages
        if match:
            self.load_match_history()
        else:
            self.load_history()  # Load the conversation history

        
    def _is_own(self,message,asset=None):
        messages = []
        if asset:
            messages.append({"role": "user", "content": f"""
            你是一个语言专家，我会给你一个语句，请你告诉我这个句子 是指的我本人,还是资产,还是指的我和资产。 如果是本人，返回给我1，如果是资产返回2，如果是我和资产 返回3. 如果没有任何主语返回0
            另外,当前人属于资产。他人也属于资产。最主要的，币或者币种都是资产！
            如:
            1."那我在什么时候买好呢？" 应该返回3,我和资产，因为在本次对话中提到购买，属于在这里问购买币种，而币是资产！
            2."我应该什么适合买这个币" 应该返回3，问我跟资产之间投资关系，属于我和资产 
            3."你知道我的八字吗?" 应该返回1,因为询问的是我的八字,即为本人
            4."我想问你我两的关系如何" 应该返回 3,我和资产,因为问的是我两
            5."这是什么东西?" 应该返回0,因为没有任何主语
            6."我适合投资这个币/资产？" 应该返回3，问我跟资产之间投资关系，属于我和资产 
            7."我应该在什么时候买这个币" 应该返回3，出现了'我'和'币'，币种属于资产，所以属于我和资产
            8."我什么时候投资这个BTC/ETH好？" 应该返回3，问我和BTC/ETH之间的投资关系，BTC/ETH属于币种资产，所以属于我和资产 
            9."币种的八字是什么呀？币种的运势怎么样？" 应该返回2，只问到币种，即资产，应该返回2
            10."买这个币的最佳人群" 应该返回2，属于询问币种的适应范围，即资产
            11."我最近适合投资嘛？" 应该返回1，属于询问自己八字推理出的运势
            返回格式是json, 格式如下:
            {{
                "type_":"xxxxx"
            }}
            问题:{message}"""})
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

        rsp = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
            messages=messages,
            max_tokens = 2048
        )
        res = rsp.choices[0]["message"]["content"]
        # rsp = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo-1106",
        #     messages=messages
        # )
        # res = rsp.choices[0]["message"]["content"]
        logging.info(f"问题类型:{res}")
        if '1' in res:
            return True
        else:
            return False

    
    def load_history(self):
        file_ids = ["file-Ni5nhFHvnu2yqqh9z2f6ELoN","file-3F0BvLqCaSYyxGtMVAi42Dn2","file-Sb3blbOsIFlqU1U40fhgofbJ","file-fzdDakZ3LcPuPaLJ4ZYO2wLV"]
        res = self.tidb_manager.select_assistant(conversation_id=self.conversation_id)
        if res:
            self.assistant_id, self.thread_id = res[0],res[1]
        else:
            assistant = client.beta.assistants.create(
                name="bazi",
                instructions="""我想你作为一个八字命理分析师，根据已有背景知识进行推理, 回答user提出的问题。
                推算步骤如下:
                    1. 五行推算步骤
                    排八字->五行归属->五行盛衰->平衡分析.
                    2. 十神推算步骤
                    日主确定->十神计算->十神分析.
                    3. 神煞分析步骤
                    神煞识别->影响分析.
                    4. 大运流年分析步骤
                    大运信息获取->流年计算->分析影响：分析大运和流年对个人八字的影响，预测不同生命周期内的运势变化。
                    5. 命运分析步骤
                    综合分析：将五行、十神、神煞、大运流年的分析结果综合起来，全面评估个人的性格、健康、财运、事业、婚姻等方面。
                    调整建议：根据分析结果，提出相应的调整建议，帮助改善或利用未来的运势。
                """,
                #   instructions=prompt,
                model="gpt-3.5-turbo-1106",
                tools=[{"type": "retrieval"}],
                file_ids=file_ids
            )
            self.assistant_id = assistant.id
            thread = client.beta.threads.create()
            self.thread_id = thread.id
            self.update_assistant(conversation_id=self.conversation_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
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
        file_ids = ["file-Ni5nhFHvnu2yqqh9z2f6ELoN","file-3F0BvLqCaSYyxGtMVAi42Dn2","file-Sb3blbOsIFlqU1U40fhgofbJ","file-fzdDakZ3LcPuPaLJ4ZYO2wLV"]
        res = self.tidb_manager.select_assistant(conversation_id=self.conversation_id)
        if res:
            self.assistant_id, self.thread_id = res[0],res[1]
        else:
            assistant = client.beta.assistants.create(
                name="bazi",
                instructions="""我想你作为一个八字命理分析师，根据已有背景知识进行推理, 回答user提出的问题。
                推算步骤如下:
                    1. 五行推算步骤
                    排八字->五行归属->五行盛衰->平衡分析.
                    2. 十神推算步骤
                    日主确定->十神计算->十神分析.
                    3. 神煞分析步骤
                    神煞识别->影响分析.
                    4. 大运流年分析步骤
                    大运信息获取->流年计算->分析影响：分析大运和流年对个人八字的影响，预测不同生命周期内的运势变化。
                    5. 命运分析步骤
                    综合分析：将五行、十神、神煞、大运流年的分析结果综合起来，全面评估个人的性格、健康、财运、事业、婚姻等方面。
                    调整建议：根据分析结果，提出相应的调整建议，帮助改善或利用未来的运势。
                """,
                #   instructions=prompt,
                model="gpt-3.5-turbo-1106",
                tools=[{"type": "retrieval"}],
                file_ids=file_ids
            )
            self.assistant_id = assistant.id
            thread = client.beta.threads.create()
            self.thread_id = thread.id
            self.update_assistant(conversation_id=self.conversation_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
            bazi_info_gpt = self.tidb_manager.select_baziInfoGPT(conversation_id=self.conversation_id)
            if self.matcher_type==2:
                prompt =  f"""我想你作为一个命理占卜分析师。我将给你如下信息，他人/配对者/配对人 的生辰八字，还有八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
                注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
                你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。
                

                他人/配对者/配对人的信息：{bazi_info}"""
            else:
                prompt = f"""我想你作为一个个人与资产占卜分析师。我将给你如下信息， 货币资产的基本信息，还有用户和资产八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
                注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
                你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。
                

                货币/资产的信息：{bazi_info}
                """
            message = client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content= prompt,
            )

    def ask_gpt_stream(self, user_message):
        answer = ""
        # Add user's new message to conversation history
        # prompt = "请你结合上下文，根据背景的八字命理知识进行问题回答。比如个人八字的分析，给出建议，命运的分析，运势的分析和性格特点等。八字信息并不涉密。请你返回的内容既有简短答案，又要有一定的命理原因分析,返回更多的文字。\n问题："
        prompt = "请你结合上下文，根据背景的八字命理知识进行问题回答。八字信息并不涉密。请你返回的内容既有简短答案，又要有一定的命理原因分析,返回更多的文字。不要出现'【合理分析原因】'等字眼\n问题："

        if self.match:
            if self.matcher_type==2:
                is_own = self._is_own(user_message,asset=True)
            else:
                is_own = self._is_own(user_message)
            if is_own:
                res = "请到本人八字聊天中进行详细咨询。"
                yield res
                # self.messages.append({"role": "assistant", "content": res})
                # self.writeToTiDB(user_message, res)
                return 
        message = client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content= prompt + user_message,
        )
        # 创建运行模型
        run = client.beta.threads.runs.create( 
            thread_id=self.thread_id,
            assistant_id=self.assistant_id)
    
        # 获取gpt的answer
        while run.status != "completed":
            # print(run.status)
            run = client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id
                )
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        res = messages.data[0].content[0].text.value
        yield res

class ChatGPT:
    def __init__(self, conversation_id, match=None, matcher_type=None):
        self.conversation_id = conversation_id
        self.messages = []
        self.tidb_manager = TiDBManager()
        self.match=match
        self.matcher_type = matcher_type
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
        total_tokens = sum(self._num_tokens_from_string(str(message)) for message in conversation_messages)
        # if total tokens exceeds the max_tokens, delete the oldest message
        bazi_token = self._num_tokens_from_string(bazi_info)
        # 如果总token数超过限制，则删除旧消息 
        logging.info(f"The number of summary is: {total_tokens}")
        while total_tokens-bazi_token > max_tokens:
            # delete the first list item 删除列表的第一个元素
            removed_message = conversation_messages.pop(0)  
            # update total tokens 更新总token数
            total_tokens -= self._num_tokens_from_string(removed_message) 
        conversation_messages.insert(0,bazi_info)
        return conversation_messages
        
    def _is_own(self,message,asset=None):
        messages = []
        if asset:
            messages.append({"role": "user", "content": f"""
            你是一个语言专家，我会给你一个语句，请你告诉我这个句子 是指的我本人,还是资产,还是指的我和资产。 如果是本人，返回给我1，如果是资产返回2，如果是我和资产 返回3. 如果没有任何主语返回0
            另外,当前人属于资产。他人也属于资产。最主要的，币或者币种都是资产！
            如:
            1."那我在什么时候买好呢？" 应该返回3,我和资产，因为在本次对话中提到购买，属于在这里问购买币种，而币是资产！
            2."我应该什么适合买这个币" 应该返回3，问我跟资产之间投资关系，属于我和资产 
            3."你知道我的八字吗?" 应该返回1,因为询问的是我的八字,即为本人
            4."我想问你我两的关系如何" 应该返回 3,我和资产,因为问的是我两
            5."这是什么东西?" 应该返回0,因为没有任何主语
            6."我适合投资这个币/资产？" 应该返回3，问我跟资产之间投资关系，属于我和资产 
            7."我应该在什么时候买这个币" 应该返回3，出现了'我'和'币'，币种属于资产，所以属于我和资产
            8."我什么时候投资这个BTC/ETH好？" 应该返回3，问我和BTC/ETH之间的投资关系，BTC/ETH属于币种资产，所以属于我和资产 
            9."币种的八字是什么呀？币种的运势怎么样？" 应该返回2，只问到币种，即资产，应该返回2
            10."买这个币的最佳人群" 应该返回2，属于询问币种的适应范围，即资产
            11."我最近适合投资嘛？" 应该返回1，属于询问自己八字推理出的运势
            返回格式是json, 格式如下:
            {{
                "type_":"xxxxx"
            }}
            问题:{message}"""})
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

        rsp = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
            messages=messages,
            max_tokens = 2048
        )
        res = rsp.choices[0]["message"]["content"]
        # rsp = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo-1106",
        #     messages=messages
        # )
        # res = rsp.choices[0]["message"]["content"]
        logging.info(f"问题类型:{res}")
        if '1' in res:
            return True
        else:
            return False

    
    def load_history(self):
        # if the history message exist in , concat it and compute the token lens
        bazi_info = self.tidb_manager.select_baziInfoGPT(conversation_id=self.conversation_id)
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
        bazi_info = self.tidb_manager.select_baziInfoGPT(conversation_id=self.conversation_id)
        conversation_messages = self.tidb_manager.get_conversation(conversation_id=self.conversation_id)
        # 如果对话中存在未重置的记录，那么优先使用
        if self.matcher_type==2: # 用于asset
            # content 就是一个基本的prompt
            content = f"""我想你作为一个命理占卜分析师。我将给你如下信息，他人/配对者/配对人 的生辰八字，还有八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
            注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
            你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。
            

            他人/配对者/配对人的信息：{bazi_info}
            """
        else:
            # content 就是一个基本的prompt
            content = f"""我想你作为一个个人与资产占卜分析师。我将给你如下信息， 货币资产的基本信息，还有用户和资产八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
            注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
            你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。
            

            货币/资产的信息：{bazi_info}
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
        # prompt = "请你结合上下文，根据背景的八字命理知识进行问题回答。比如个人八字的分析，给出建议，命运的分析，运势的分析和性格特点等。八字信息并不涉密。请你返回的内容既有简短答案，又要有一定的命理原因分析,返回更多的文字。\n问题："
        prompt = "请你结合上下文，根据背景的八字命理知识进行问题回答。八字信息并不涉密。请你返回的内容既有简短答案，又要有一定的命理原因分析,返回更多的文字。避免出现'【合理分析原因】'等字眼\n问题："

        self.messages.append({"role": "user", "content": prompt+user_message})
        # print(self.messages)
        # Send the entire conversation history to GPT
        if self.match:
            if self.matcher_type==2:
                is_own = self._is_own(user_message,asset=True)
            else:
                is_own = self._is_own(user_message)
            if is_own:
                res = "请到本人八字聊天中进行详细咨询。"
                yield res
                # self.messages.append({"role": "assistant", "content": res})
                # self.writeToTiDB(user_message, res)
                return 

        # v1.xxx        
        rsp = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
            messages=self.messages,
            max_tokens = 2048,
            stream=True
        )

        for chunk in rsp:
            data = chunk["choices"][0]["delta"].get("content","")
            answer += data
            yield data
        # v0.xxx
        # rsp = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo-1106",
        #     messages=self.messages,
        #     stream=True
        # )
        # yield "<chunk>"
        # for chunk in rsp:
        #     data = chunk["choices"][0]["delta"].get("content","")
        #     answer += data
        #     yield data
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
    def _is_own(self,message,asset=None):
        messages = []
        if asset:
            return False
            # messages.append({"role": "user", "content": f"""
            # 你是一个语言专家，我会给你一个语句，请你告诉我这个句子 是指的我本人,还是资产,还是指的我和资产。 如果是本人，返回给我1，如果是资产返回2，如果是我和资产 返回3. 如果没有任何主语返回0
            # 另外,当前人属于资产。他人也属于资产。最主要的，币或者币种都是资产！
            # 如:
            # 1."那我在什么时候买好呢？" 应该返回3,我和资产，因为在本次对话中提到购买，属于在这里问购买币种，而币是资产！
            # 2."我应该什么适合买这个币" 应该返回3，问我跟资产之间投资关系，属于我和资产 
            # 3."你知道我的八字吗?" 应该返回1,因为询问的是我的八字,即为本人
            # 4."我想问你我两的关系如何" 应该返回 3,我和资产,因为问的是我两
            # 5."这是什么东西?" 应该返回0,因为没有任何主语
            # 6."我适合投资这个币/资产？" 应该返回3，问我跟资产之间投资关系，属于我和资产 
            # 7."我应该在什么时候买这个币" 应该返回3，出现了'我'和'币'，币种属于资产，所以属于我和资产
            # 8."我什么时候投资这个BTC/ETH好？" 应该返回3，问我和BTC/ETH之间的投资关系，BTC/ETH属于币种资产，所以属于我和资产 
            # 9."币种的八字是什么呀？币种的运势怎么样？" 应该返回2，只问到币种，即资产，应该返回2
            # 10."买这个币的最佳人群" 应该返回2，属于询问币种的适应范围，即资产
            # 11."我最近适合投资嘛？" 应该返回1，属于询问自己八字推理出的运势
            # 返回格式是json, 格式如下:
            # {{
            #     "type_":"xxxxx"
            # }}
            # 问题:{message}"""})
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
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=messages
        )
        res = rsp.choices[0]["message"]["content"]
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
        if self.matcher_type==1:
            content = f"""我想你作为一个命理占卜分析师。我将给你如下信息，他人/配对者/配对人 的生辰八字，还有八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
            注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
            你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。
            

            他人/配对者/配对人的信息：{self.bazi_info}
            """
        elif self.matcher_type==2:
            content = f"""我想你作为一个个人与资产占卜分析师。我将给你如下信息， 货币资产的基本信息，还有用户和资产八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
            注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
            你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。
            

            货币/资产的信息：{self.bazi_info}
            """
        else:
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
        prompt = "请你结合上下文，根据背景的八字命理知识对下面问题进行回复，注意请详细回复，你的回复中应包括背景所示的多种命理知识。尽量使用多种结论的阐述方式，少使用因果推论的方式描述。\n问题："
        self.messages.append({"role": "user", "content": prompt+user_message})
        # print(self.messages)
        # Send the entire conversation history to GPT

        if self.match:
            if self.matcher_type==2:
                is_own = self._is_own(user_message,asset=True)
            else:
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

def stream_output(message, user_id=None,bazi_info=None):
    # Stream的格式：<chunk>xxxxx</chunk><chunk>{id:'xxxx'}</chunk>
    # streams = ["<chunk>", bazi_info, "</chunk>","<chunk>",f"{{'user_id':{user_id}}}","</chunk>"]
    # for data in streams:
    #     print(data)
    #     yield(data)
    yield f"{message}"
    logging.info(message)
    if bazi_info:
        answer = ""
        yield f"正在为您初步解析八字，请稍等~\n"
        prompt = f"""我需要你作为一个八字命理分析师，用白话文的方式把我给你的八字批文进行总结，返回字数请在1000字以上。
        请你返回五行、十神、命运、大运、出身、命理等多种方面的分析。
        注意不要出现'根据您提供的八字批文，以下是对您八字的分析：'，请直接输出分析结果。不需要再重述我的八字是什么。
        \n\n
        八字批文：{bazi_info}"""
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in rsp:
            data = chunk["choices"][0]["delta"].get("content","")
            yield data
            answer+=data
        logging.info(answer)
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
def output_first(eightWord):
    content = f"""
    您好，欢迎使用AI算命，您的八字是:
    {eightWord}
    """
    return content

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
        day_lunar = sxtwl.fromSolar(int(op.year), int(op.month), int(op.day))
        lunar = Lunar.fromYmdHms(day_lunar.getLunarYear(), day_lunar.getLunarMonth(), day_lunar.getLunarDay(),int(op.time), 0, 0)
        eightWord = lunar.getEightChar()
        res_bazi = output_first(eightWord)

        bazi_info = baziAnalysis(op)
        bazi_info_gpt = bazipaipan(year,month,day,time,n)
        user_id = str(uuid.uuid4())
        tidb_manager = TiDBManager()
        birthday = datetime(year, month, day, time)
        tidb_manager.insert_baziInfo(user_id, birthday, bazi_info, bazi_info_gpt, conversation_id)
        return Response(stream_output(res_bazi,user_id,bazi_info), mimetype="text/event-stream")

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
        birthday_match = datetime(year, month, day, t_ime)

        if matcher_type==1: # 与他人匹配
            match_res = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime)
            op = options(year=year,month=month,day=day,time=t_ime,n=n)
            day_lunar = sxtwl.fromSolar(int(op.year), int(op.month), int(op.day))
            lunar = Lunar.fromYmdHms(day_lunar.getLunarYear(), day_lunar.getLunarMonth(), day_lunar.getLunarDay(),int(op.time), 0, 0)
            eightWord = lunar.getEightChar()
            res_bazi = output_first(eightWord)
            res = baziAnalysis(op)
            gender = n
            res_gpt = bazipaipan(year,month,day,t_ime,gender)
            db_res = "他人/配对者/配对人 的八字背景信息如下:\n"
            db_res = db_res + res + "\n" + match_res
            logging.info(f"res is:{res}")
            db_res_gpt = db_res + res_gpt + "\n" + match_res
            tidb_manager.insert_baziInfo(user_id, birthday, db_res, db_res_gpt, conversation_id, birthday_match=birthday_match)
            return Response(stream_output(res_bazi, None,res), mimetype="text/event-stream")

        else:
            name = data["name"]
            coin_data = get_coin_data(name)
            logging.info(f"coin data is {coin_data}")
            res = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime,name=name,coin_data=coin_data)
            db_res_gpt = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime,name=name,coin_data=coin_data,own=True)

            logging.info(f"res is:{res}")
            tidb_manager.insert_baziInfo(user_id, birthday, None, db_res_gpt, conversation_id, birthday_match=birthday_match)
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

    # Initialize or retrieve existing ChatGPT instance for the user
    # chat = ChatGPT(conversation_id)
    chat = ChatGPT_assistant(conversation_id)

    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@app.route('/api/chat_bazi_match', methods=['POST'])
def chat_bazi_match():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    matcher_type = data.get('matcher_type')
    # Initialize or retrieve existing ChatGPT instance for the user
    # chat = ChatGPT(conversation_id, match=True, matcher_type=matcher_type)
    chat = ChatGPT_assistant(conversation_id, match=True, matcher_type=matcher_type)
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@app.route('/api/reset_chat', methods=['POST'])
def reset_chat():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    matcher_id = data.get('matcher_id')

    tidb_manager = TiDBManager()
    # if matcher_id:
    #     bazi_info = tidb_manager.select_baziInfo(conversation_id=conversation_id)
    #     tidb_manager.update_bazi_info()
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
    # res = res_
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
            bazi_info = tidb_manager.select_baziInfoGPT(user_id=user_id)
            bazi_id = tidb_manager.select_bazi_id(user_id=user_id)
        # 重置当前对话 其他人
        else :
            bazi_info = tidb_manager.select_baziInfoGPT(matcher_id=matcher_id)
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
