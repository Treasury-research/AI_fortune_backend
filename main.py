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
logging.basicConfig(filename='AI_fortune.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
# 跨域支持
CORS(app, resources=r'/*')

# Your existing ChatGPT class here (no changes needed)
class TiDBManager:
    def __init__(self):
        self.db = pool.connection()


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
        return True
        # except:
        #     return False

    def select_asset(self, user_id):
        with self.db.cursor() as cursor:
            sql = "SELECT name, birthday FROM AI_fortune_assets WHERE user_id=%s OR is_public=1"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchall()
            if result:
                return result
            else:
                return False


    def reset_conversation(self, conversation_id):
        try:
            with self.db.cursor() as cursor:
                sql = "UPDATE AI_fortune_conversation SET is_reset = 1 WHERE conversation_id = %s"
                cursor.execute(sql, (conversation_id,))
            self.db.commit()
            return True
        except:
            logging.info(f"database reset conversation error where conversation_id = {conversation_id}")
            return False


    def insert_conversation(self, user_id, conversation_id, human_message=None, AI_message=None):
        try:
            generated_uuid = str(uuid.uuid4())
            with self.db.cursor() as cursor:
                if human_message and AI_message:
                    sql = """
                        INSERT INTO AI_fortune_conversation (id, user_id, conversation_id, human, AI) VALUES (%s, %s, %s, %s, %s)
                        """
                    cursor.execute(sql, (generated_uuid, user_id, conversation_id, human_message, AI_message))
                else:
                    logging.info(f"Insert conversation error where conversation_id = {conversation_id}")
                    return False
            self.db.commit()
            logging.info(f"Insert conversation success where conversation_id = {conversation_id}")
            return True
        except:
            return False

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
    def insert_baziInfo(self, user_id, birthday, bazi_info, birthday_match=None):
        generated_uuid = str(uuid.uuid4())
        with self.db.cursor() as cursor:
            if birthday_match:
                sql = """
                    INSERT INTO AI_fortune_bazi (id, user_id, birthday, birthday_match, bazi_info) VALUES (%s, %s, %s, %s, %s)
                    """
                cursor.execute(sql, (generated_uuid, user_id, birthday, birthday_match, bazi_info))
            else:
                sql = """
                    INSERT INTO AI_fortune_bazi (id, user_id, birthday, bazi_info) VALUES (%s, %s, %s, %s)
                    """
                cursor.execute(sql, (generated_uuid, user_id, birthday, bazi_info))
        self.db.commit()

    def select_baziInfo(self, user_id):
        with self.db.cursor() as cursor:
            sql = "SELECT bazi_info FROM AI_fortune_bazi WHERE user_id=%s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return False

    def select_birthday(self, user_id):
        with self.db.cursor() as cursor:
            sql = "SELECT birthday FROM AI_fortune_bazi WHERE user_id=%s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return False

class ChatGPT:
    def __init__(self, user_id, conversation_id, match=None):
        self.conversation_id = conversation_id
        self.messages = []
        self.tidb_manager = TiDBManager()
        # self.user_id = self.tidb_manager.get_user_id(self.conversation_id)
        self.user_id = user_id
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
        while total_tokens > max_tokens:
            # delete the first list item 删除列表的第一个元素
            removed_message = conversation_messages.pop(0)  
            # update total tokens 更新总token数
            total_tokens -= self._num_tokens_from_string(removed_message) 
        return conversation_messages

    def load_history(self):
        # if the history message exist in , concat it and compute the token lens
        bazi_info = self.tidb_manager.select_baziInfo(self.user_id)
        conversation_messages = self.tidb_manager.get_conversation(self.conversation_id)
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


    def load_match_history(self):
        # if the history message exist in , concat it and compute the token lens
        bazi_info = self.tidb_manager.select_baziInfo(self.user_id)
        conversation_messages = self.tidb_manager.get_conversation(self.conversation_id)
        # 如果对话中存在未重置的记录，那么优先使用
        # content 就是一个基本的prompt
        content = f"""我想你作为一个命理占卜分析师。我将给你如下信息，本人的生辰八字和需要配对者的生辰八字，还有八字配对的结果。你的工作是根据我给定的信息作为整个对话的背景知识进行问题的回答。
        注意，在你回答的时候请避免使用因果推论的方式进行回答，即回答时尽可能给出结论和结论的分析，避免出现'因为xxx,所以xxx'等的推论。
        你的回答输出时文字不能出现'依据占卜...','请记住，这些分析是基于传统八字学的原则....'等提醒言论。


        信息：{bazi_info}
        """
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
        self.tidb_manager.insert_conversation(self.user_id, self.conversation_id, human, AI)

    def ask_gpt_stream(self, user_message):
        answer = ""
        # Add user's new message to conversation history
        self.messages.append({"role": "user", "content": user_message})
        # print(self.messages)
        # Send the entire conversation history to GPT
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=self.messages,
            stream=True
        )
        yield "<chunk>"
        for chunk in rsp:
            data = chunk["choices"][0]["delta"].get("content","")
            answer += data
            yield data
        yield f"</chunk><chunk>{{'user_id':{self.user_id}}}</chunk>"
        # Add GPT's reply to conversation history
        self.messages.append({"role": "assistant", "content": answer})
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

def stream_output(message, user_id):
    # Stream的格式：<chunk>xxxxx</chunk><chunk>{id:'xxxx'}</chunk>
    # streams = ["<chunk>", bazi_info, "</chunk>","<chunk>",f"{{'user_id':{user_id}}}","</chunk>"]
    # for data in streams:
    #     print(data)
    #     yield(data)
    yield f"<chunk>{message}</chunk><chunk>{{'user_id':{user_id}}}</chunk>"



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
        year = request.get_json().get("year")
        month = request.get_json().get("month")
        day = request.get_json().get("day")
        try:
            year = int(year)
            month = int(month)
            day = int(day)
        except:
            return jsonify({"error":"无效的数据格式"}, 400)
        time = request.get_json().get("time")
        n = request.get_json().get("n")
        time = int(int(time.split("-")[0])  + int(time.split("-")[1]) / 2 ) # 提取开始小时
        op = options(year=year,month=month,day=day,time=time,g=g,b=b,n=n,r=r)
        bazi_info = baziAnalysis(op)
        user_id = str(uuid.uuid4())
        tidb_manager = TiDBManager()
        birthday = datetime(year, month, day, time)
        tidb_manager.insert_baziInfo(user_id, birthday, bazi_info)
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
        return Response(output, content_type="text/plain; charset=utf-8")


@app.route('/api/baziMatch',methods=['POST','GET'])
def baziMatchRes():
    if request.method =="POST":
        tidb_manager = TiDBManager()
        data = request.get_json()
        year,month,day,t_ime,user_id,n = data['year'], data['month'], data['day'], data['time'], data['user_id'], data['n']
        try:
            year = int(year)
            month = int(month)
            day = int(day)
        except:
            return jsonify({"error":"无效的数据格式"}, 400)
        t_ime = int(int(t_ime.split("-")[0])  + int(t_ime.split("-")[1]) / 2 ) # 提取开始小时
        birthday = tidb_manager.select_birthday(user_id)
        bazi_info = tidb_manager.select_baziInfo(user_id)
        op = options(year=year,month=month,day=day,time=t_ime,n=n)
        bazi_info_match = baziAnalysis(op)
        total_score, bb, c, yh, rh, rrh, ez = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime)
        res = f"本人的八字及其批文：{bazi_info} \n 匹配者的八字及其批文：{bazi_info_match} \n 两者八字匹配得分："
        # res += f"""命宫：{bb}分
        #             此项为30分 说明：以东四命与西四命之说来合，如果相合，那么在购房时，应买与自己命宫相合的房子。
        # 年支同气：{c}分
        #             此项为20分 说明：如寅卯辰会东方木气，虎兔龙结合的机缘就大于其它属相；巳午未会南方火气，蛇马羊结合的机缘就大于其它属相；申酉戌会西方金气，猴鸡狗结合的机缘就大于其它属相；亥子丑会北方水气，猪鼠牛结合的机缘就大于其它属相。
        # 月令合：{yh}分
        #             此项为5分 说明：男女生月相同者互相间也是很有缘份的
        # 日干相合：{rh}分
        #             此项为25分 说明：谓日干舒配得所？日干五行相同，一阴一阳的组合男女结合的机缘最大，如甲日干逢乙日干，庚日干逢辛日干之类。
        # 天干五合：{rrh}分
        #             此项为5分 说明：其次是天干五合，如甲日干逢己日干，庚日干逢乙日干之类。再次则是比和或相生。
        # 子女同步：{ez}分
        #             此项为15分 说明：何谓子女同步？西方的科学家在探索男女结合的奥秘时提出了 " 性染色体论 " ，我们东方人在四柱预测中看头胎子女的性别，男女双方的八字中头胎子女的性别必须一致。
        # 总分：{total_score}分"""
        res += f"""
            1. 命宫相合：{bb}分
                此项为30分 说明：根据两个八字的命宫是否相合来评分。命宫相合通常意味着两者在性格、命运走向等方面有较好的匹配度。

            2. 年支同气：{c}分
                此项为20分 说明：考虑两个八字的年支（生肖）是否归属于相同的五行方位。例如，寅卯辰属东方木气，相同方位的年支表示在天性、运势方面可能相辅相成。

            3. 月令相合：{yh}分
                此项为5分 说明：如果两个八字的月令（出生月的地支）相合或相生，这表示两者在一年中的能量周期上可能存在共鸣。

            4. 日干相合：{rh}分
                此项为25分 说明：日干代表个体的本质和核心特质。如果两个八字的日干相合或相生，如一阴一阳的组合，这预示着两者在本质上的互补或和谐。

            5. 天干五合：{rrh}分
                此项为5分 说明：考察两个八字的天干是否形成五行上的相合或相生关系，这关系到两者在五行动态平衡中的互动。

            6. 综合匹配度：{ez}分
                此项为15分 说明：综合考虑两个八字在各方面的相合程度，包括性格、命运走向、生活习惯等方面的整体协调性。

            7. 总分：{total_score}分        
        """
        user_id = str(uuid.uuid4())
        birthday_match = datetime(year, month, day, t_ime)
        tidb_manager.insert_baziInfo(user_id, birthday, res, birthday_match=birthday_match)
        return Response(stream_output(res, user_id), mimetype="text/event-stream")


@app.route('/api/chat_bazi', methods=['POST'])
def chat_bazi():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_id = data.get('user_id')
    user_message = data.get('message')

    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT(user_id, conversation_id)
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@app.route('/api/chat_bazi_match', methods=['POST'])
def chat_bazi_match():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_id = data.get('user_id')
    user_message = data.get('message')

    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT(user_id, conversation_id, match=True)
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
    res = tidb_manager.select_asset(user_id)
    # Return the ChatGPT's response
    if res:
        return jsonify({"status": "success", "data":res}, 200)
    else:
        return jsonify({"status": "database select Error"}, 500)

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