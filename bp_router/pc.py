import sxtwl
import json
import os
import time
from flask import Flask, Response, request, stream_with_context, jsonify, make_response
import os
from datetime import datetime, timedelta
import uuid
import jwt
from eth_account import Account

from main_v2 import logging
from chat.pc import ChatGPT_assistant
from database.mysql_db import TiDBManager
from database.redis_db import RedisManager
from bazi_info.bazi import baziAnalysis
from bazi_info.bazi_match import baziMatch
from bazi_info.bazi_gpt import bazipaipan
from utils.options_class import options
from utils.util import *
from utils.question_rec import rec_question
from flask import Blueprint
pc = Blueprint('pc', __name__)

@pc.route('/baziAnalysis',methods=['POST','GET'])
def baziAnalysis_stream():
    if request.method =="POST":
        logging.info(f"baziAnalysis POST_data: {request.get_json()}") 
        year = request.get_json().get("year")
        month = request.get_json().get("month")
        day = request.get_json().get("day")
        time = request.get_json().get("time")
        name = request.get_json().get("name")
        conversation_id = request.get_json().get("conversation_id")
        gender = request.get_json().get("n")
        lang = request.headers.get('Lang')
        user_id = request.get_json().get("user_id")  #如果输入带user_id 则认为是修改信息
        try:
            year = int(year)
            month = int(month)
            day = int(day)
        except:
            return jsonify({"error":"无效的数据格式"}, 400)

        if int(time.split("-")[0])>=23:
            time = 0
        else:
            time = int(int(time.split("-")[0])/2  + int(time.split("-")[1]) / 2 ) # 提取开始小时
        op = options(year=year,month=month,day=day,time=time,g=g,b=b,n=gender,r=r)
        (mingyun_analysis,chushen_analysis),bazi_info_gpt = bazipaipan(year,month,day,time,gender,name=name)
        bazi_info = baziAnalysis(op,mingyun_analysis,chushen_analysis)
        tidb_manager = TiDBManager()
        birthday = datetime(year, month, day, time)
        first_reply = "您好，欢迎使用AI算命。\n" + bazi_info_gpt.split("---------------")[0]
        # 由于是本人，因此是插入或者修改
        # 如果user_id带有，那就是update操作，把之前的信息is_deleted设为1，表示重新开始对话。（因为背景信息会有所变化，对话重新开始）
        if user_id:
            tidb_manager.update_reset_delete(conversation_id=conversation_id)
        else:
            user_id = str(uuid.uuid4())
        tidb_manager.insert_bazi_chat(user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply)
        tidb_manager.upsert_user(user_id, birthday=birthday, name=name, gender=gender) # gender 0 为男，1 为女
        # 如果需要翻译成英文
        if lang=='En':
            result_text = translate(first_reply)
        else:
            result_text = first_reply
        return Response(stream_output(None,user_id,result_text), mimetype="text/event-stream")


@pc.route('/baziMatch',methods=['POST','GET'])
def baziMatchRes():
    if request.method =="POST":
        tidb_manager = TiDBManager()
        data = request.get_json()
        logging.info(f"data is :{data}")
        year,month,day,t_ime,user_id,gender = data['year'], data['month'], data['day'], data['time'], data['user_id'], data['n']
        name = data.get("name")
        update = date.get("update")
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
        birthday_user = tidb_manager.select_user(user_id,birthday=True)
        birthday = datetime(year, month, day, t_ime)

        if matcher_type==1: # 与他人匹配
            match_res = baziMatch(birthday_user.year,birthday_user.month,birthday_user.day,birthday_user.hour, year,month,day,t_ime)
            op = options(year=year,month=month,day=day,time=t_ime,n=gender)
            (mingyun_analysis,chushen_analysis),bazi_info_gpt = bazipaipan(year,month,day,t_ime,gender,name)
            bazi_info = baziAnalysis(op,mingyun_analysis,chushen_analysis)
            head = f"他人/配对者/配对人, {name}的八字背景信息如下:\n"
            db_res = head + bazi_info + "\n" + match_res
            db_res_gpt = head + bazi_info_gpt + "\n" + match_res
            first_reply = "您好，欢迎使用AI算命。\n" + bazi_info_gpt.split("---------------")[0]
            if update:
                tidb_manager.update_reset_delete(conversation_id=conversation_id)
                matcher_id = tidb_manager.select_chat_bazi(conversation_id=conversation_id, matcher_id=True)
            else:
                # 插入匹配者信息
                matcher_id = str(uuid.uuid4())
            tidb_manager.upsert_matcherPerson(matcher_id, gender, birthday, user_id, name=name)
            # 插入八字信息
            tidb_manager.insert_bazi_chat(user_id, conversation_id, db_res, db_res_gpt, first_reply, matcher_id=matcher_id, matcher_type=matcher_type)
            # 如果需要翻译成英文
            if lang=="En":
                result_text = translate(first_reply)
            else:
                result_text = first_reply
            return Response(stream_output(None, None,result_text), mimetype="text/event-stream")

        elif matcher_type==2:
            coin_data = get_coin_data(name)
            logging.info(f"coin data is {coin_data}")
            res = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime,name=name,coin_data=coin_data)
            db_res_gpt = baziMatch(birthday.year,birthday.month,birthday.day,birthday.hour, year,month,day,t_ime,name=name,coin_data=coin_data,own=True)

            logging.info(f"res is:{res}")
            tidb_manager.insert_baziInfo(user_id, birthday, res, db_res_gpt, conversation_id, birthday_match=birthday_match,first_reply=db_res_gpt)
            return Response(stream_output(res, None), mimetype="text/event-stream")

@pc.route('/get_bazi_info', methods=['POST'])
def get_bazi_info():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    tidb_manager = TiDBManager()
    bazi_info = tidb_manager.select_chat_bazi(conversation_id=conversation_id, bazi_info=True)
    # Initialize or retrieve existing ChatGPT instance for the user
    return Response(stream_output(bazi_info,), mimetype="text/event-stream")

@pc.route('/chat_bazi', methods=['POST'])
def chat_bazi():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    lang = request.headers.get('Lang')
    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT_assistant(conversation_id, lang=lang, matcher_type=0)
    logging.info(f"conversation_id {conversation_id}, message {user_message}")
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@pc.route('/chat_bazi_match', methods=['POST'])
def chat_bazi_match():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    matcher_type = data.get('matcher_type')
    lang = request.headers.get('Lang')
    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT_assistant(conversation_id, lang=lang, match=True, matcher_type=matcher_type)
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@pc.route('/reset_chat', methods=['POST'])
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


@pc.route('/assets_insert', methods=['POST'])
def asset_insert():
    data = request.get_json()
    name = data.get('name')
    birthday = data.get('birthday')
    user_id = data.get('user_id')
    tidb_manager = TiDBManager()
    # 如果是公共的财产时间，则不用记录user_id
    if user_id:
        res = tidb_manager.upsert_asset(name,birthday,user_id)
    # 如果是用户单独导入的财产，记录user_id
    else:
        res = tidb_manager.upsert_asset(name,birthday)
    # Return the ChatGPT's response
    if res:
        return jsonify({"status": "success"}, 200)
    else:
        return jsonify({"status": "database insert Error"}, 500)

@pc.route('/assets_select', methods=['POST'])
def asset_select():
    data = request.get_json()
    user_id = data.get('user_id')
    tidb_manager = TiDBManager()
    _res = tidb_manager.select_asset(user_id)
    res = [(name, birthday) for name, birthday, _ in _res]
    # Return the ChatGPT's response
    if res:
        return jsonify({"status": "success", "data":res}, 200)
    else:
        return jsonify({"status": "database select Error"}, 500)

@pc.route('/api/question_rec', methods=['POST'])
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
        if matcher_type == 1:
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
                # 定义问题列表
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
                questions =  [
                    "How is my financial fortune?",
                    "When can I get married?",
                    "What kind of job is right for me?",
                    "How to make up for the lack of fire in the five elements?",
                    "What's my lucky number?",
                    "When can I have a girlfriend?",
                    "Any suggestions for improving Feng Shui and the Five Elements?"
                ]
            # 定义问题列表
            else:
                questions = [
                    "从我的财运怎么样？",
                    "我什么时候能结婚？",
                    "什么样的工作适合我？",
                    "五行缺火该怎么补？",
                    "我的幸运数字是什么？",
                    "我什么时候走桃花运？",
                    "有什么改善风水和五行的建议？"
                ]
        # 从问题库中随机给出
        result = random.sample(questions, 3)

    if result:
        return jsonify({"status": "success", "data":result}, 200)
    else:
        return jsonify({"status": "database select Error"}, 500)


@pc.route('/translate',methods=['POST'])
def translate_():
    request_data = request.get_json()
    text = request_data.get('text')
    res = translate(text)
    if res:
        return Response(stream_output(None, None, res), mimetype="text/event-stream")
    else:
        return jsonify({"status": f"google translate error!"}, 500)

@app.route('/login',methods=['POST'])
def loginDto():
    data = request.get_json()
    message = data.get('message')
    address = data.get('address')
    signature = data.get('signature')
# 验证签名
    try:
        recovered_address = Account.recover_message(text=message, signature=signature)
        if recovered_address.lower() == user_address.lower():
        # 生成nonce并存入redis 过期时间为30s
            nonce = str(uuid.uuid4())
            try:
                RedisManager = RedisManager()
                RedisManager.insert_with_expiration(key=address,value=nonce)
                return jsonify({'success': True, 'nonce': nonce})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}, 400)
        else:
            return jsonify({'success': False, 'message': 'Invalid signature'}, 401)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}, 400)


@app.route('/verify',methods=['POST'])
def verifyNonce():
    data = request.get_json()
    nonce_user = data.get('nonce')
    address = data.get('address')
    # 从Redis获取nonce
    nonce_redis = r.get(user_address)
    if nonce_redis==nonce_user:
        # 生成token 放在head中返回
        # 签名验证成功，生成JWT Token
        try:
            token = jwt.encode({
                'user_address': user_address,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)  # Token 30分钟后过期
            }, os.environ['SECRET_KEY'], algorithm='HS256')
            response = make_response(jsonify({'success': True, 'message': 'login sucess'}))
            response.headers['Authorization'] = f'Bearer {token}'
            return jsonify({'success': True}, 200)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}, 400)
    else:
        return jsonify({'success': False, 'error': 'Invalid nonce'}, 400)

@pc.before_app_request
def before_request_for_blueprint():
    token = request.headers['Authorization'].split(" ")[1]  # 假设Token前缀为Bearer
    if not token:
        return jsonify({'message': 'Token is missing!'}, 403)
    try:
        jwt.decode(token, os.environ['SECRET_KRY'], algorithms=["HS256"])
    except:
        return jsonify({'message': 'Token is invalid!'}, 403)