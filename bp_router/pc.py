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
from eth_account.messages import encode_defunct
import random

from chat.pc import ChatGPT_assistant
from database.mysql_db import TiDBManager
from database.redis_db import RedisManager
from bazi_info.bazi import baziAnalysis
from bazi_info.bazi_match import baziMatch
from bazi_info.bazi_gpt import bazipaipan
from bazi_info.asset import get_asset_rules
from utils.options_class import options
from utils.util import *
from utils.question_rec import rec_question
from flask import Blueprint
from utils.log_utils import logger as logging

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
        account = request.get_json().get("account")
        # user_id = request.get_json().get("user_id")  #如果输入带user_id 则认为是修改信息
        user_id = None
        logging.info(f"user_id :{user_id}, account:{account}")
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
        op = options(year=year,month=month,day=day,time=time,n=gender)
        (mingyun_analysis,chushen_analysis),bazi_info_gpt = bazipaipan(year,month,day,time,gender,name=name)
        bazi_info = baziAnalysis(op,mingyun_analysis,chushen_analysis)
        tidb_manager = TiDBManager()
        birthday = datetime(year, month, day, time)
        first_reply = "您好，欢迎使用AI算命。\n" + bazi_info_gpt.split("---------------")[0]
        # 由于是本人，因此是插入或者修改
        # 如果user_id带有，那就是update操作，把之前的信息is_deleted设为1，表示重新开始对话。（因为背景信息会有所变化，对话重新开始）
        # 如果有account 则是已经存储;没有account 就是修改
        if user_id not in ['',None] and account is ['',None]:
            tidb_manager.update_reset_delete(conversation_id=conversation_id)
        elif user_id in ['',None] and account in ['',None]:
            user_id = str(uuid.uuid4())
        tidb_manager.insert_bazi_chat(user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply)
        tidb_manager.upsert_user(user_id, birthday=birthday, name=name, gender=gender, account=account) # gender 0 为男，1 为女
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
        year,month,day,t_ime,user_id,gender = data.get('year'), data.get('month'), data.get('day'), data.get('time'), data.get('user_id'), data.get('n')
        name = data.get("name")
        update = data.get("update")
        matcher_type = data.get("matcher_type")
        matcher_id = data.get("matcher_id")
        lang = request.headers.get('Lang')
        try:
            if year:
                year = int(year)
                month = int(month)
                day = int(day)
                if int(t_ime.split("-")[0])>=23:
                    t_ime = 0
                else:
                    t_ime = int(int(t_ime.split("-")[0])/2  + int(t_ime.split("-")[1]) / 2 ) # 提取开始小时
                birthday = datetime(year, month, day, t_ime)
        except:
            return jsonify({"error":"无效的数据格式"}, 400)
        conversation_id = request.get_json().get("conversation_id")
        birthday_user = tidb_manager.select_user(user_id,birthday=True)
        if birthday_user is None:
            pass
        else:
            birthday_user = birthday_user[0]
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
            # 方案1： 人工手写的回复
            # 首次回复是算法预算 + 卦象 + 资产报告
            if matcher_id:
                res = tidb_manager.select_asset(matcher_id=matcher_id)
                name, birthday, report= res[0], res[1], res[2]
            guaxiang = get_guaxiang()
            background = get_background(name,birthday)

            logging.info(f"data is {birthday.year, birthday.month, birthday.day, birthday.hour}")
            first_reply_rules = get_asset_rules(name, birthday.year, birthday.month, birthday.day, birthday.hour, pc=True)
            logging.info("first_reply_rules is :{first_reply_rules}")
            # first_reply 返回值是str 数组，需要进行拼接
            first_reply_rules_str = ''.join(s +'\n' for s in first_reply_rules[:-1])
            first_reply = first_reply_rules_str + "<b>资产报告：</b>"+'\n' + report + "\n" + first_reply_rules[-1] +"\n<b>卦象：</b>"+ '\n'+ guaxiang
            (mingyun_analysis,chushen_analysis),bazi_info_gpt = bazipaipan(birthday.year, birthday.month, birthday.day,
                                                                           birthday.hour,False,name=name)
            op = options(year=birthday.year,month=birthday.month,day=birthday.day,time=birthday.hour,n=False)

            #  获取资产的八字信息
            head = f"资产的信息如下：\n"
            person_prefix = f"资产的八字信息如下：\n"
            assets_info = tidb_manager.select_infos_byid(matcher_id=matcher_id)
            saved_bazi_info = assets_info[0]
            saved_bazi_info_gpt = assets_info[1]
            saved_first_reply = assets_info[2]
            if (saved_bazi_info not in ['',None]):
                bazi_info = saved_bazi_info
            else:
                bazi_info = baziAnalysis(op,mingyun_analysis,chushen_analysis)
                tidb_manager.update_infos_in_to_asset(matcher_id=matcher_id,
                                                       bazi_info=head + first_reply +"\n" + person_prefix + bazi_info,
                                                       bazi_info_gpt='',
                                                       first_reply='')
            db_res = head + first_reply +"\n" + person_prefix + bazi_info
            db_res_gpt = head + first_reply_rules_str + "\n" + background + person_prefix + bazi_info_gpt
            tidb_manager.insert_bazi_chat("", conversation_id, db_res, db_res_gpt, first_reply, matcher_id=matcher_id, matcher_type=matcher_type)
            # 如果需要翻译成英文
            if lang=="En":
                result_text = translate(first_reply)
            else:
                result_text = first_reply
            return Response(stream_output(None, None, result_text), mimetype="text/event-stream")

@pc.route('/get_bazi_info', methods=['POST'])
def get_bazi_info():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    lang = request.headers.get('Lang')
    tidb_manager = TiDBManager()
    bazi_info = tidb_manager.select_chat_bazi(conversation_id=conversation_id, bazi_info=True)[0]
    if lang=="En":
        result_text = translate(bazi_info)
    else:
        result_text = bazi_info
    # Initialize or retrieve existing ChatGPT instance for the user
    return Response(stream_output(result_text,), mimetype="text/event-stream")

@pc.route('/chat_bazi', methods=['POST'])
def chat_bazi():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    lang = request.headers.get('Lang')
    # Initialize or retrieve existing ChatGPT instance for the user
    chat = ChatGPT_assistant(conversation_id, lang=lang, matcher_type=0,message=user_message)
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
    chat = ChatGPT_assistant(conversation_id, lang=lang, matcher_type=matcher_type,message=user_message)
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")

@pc.route('/reset_chat', methods=['POST'])
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

@pc.route('/assets_insert', methods=['POST'])
def asset_insert():
    data = request.get_json()
    name = data.get('name')
    birthday = data.get('birthday')
    user_id = data.get('user_id')
    first_reply_json = data.get('first_reply')
    tidb_manager = TiDBManager()
    # 如果是公共的财产时间，则不用记录user_id
    if user_id:
        res = tidb_manager.upsert_asset(name,birthday,user_id)
    elif first_reply_json:
        res = tidb_manager.update_asset_reply(data=first_reply_json)
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
    res = tidb_manager.select_asset(user_id,hot=True,recent_hot=True)
    # res = [(name, birthday) for name, birthday, _ in _res]
    # Return the ChatGPT's response
    # 更改财产顺序
    # 按照指定的顺序重新排序
    new_order = ['BTC', 'ETH', 'SOL']
    res['hot'] = sorted(res['hot'], key=lambda x: new_order.index(x[0]))
    if res:
        return jsonify({"status": "success", "data":res}, 200)
    else:
        return jsonify({"status": "database select Error"}, 500)

@pc.route('/question_rec', methods=['POST'])
def question_rec():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    matcher_type = data.get('matcher_type')
    lang = request.headers.get('Lang')
    logging.info(f"matcher_type is :{matcher_type}")
    # 获取精确批文 和 thread_id
    tidb_manager = TiDBManager()
    if user_message:
        bazi_info = tidb_manager.select_chat_bazi(conversation_id=conversation_id,bazi_info=True)[0]
        # 如果user_message存在。 说明非首次回复
        if lang=="En":
            bazi_info = translate(bazi_info)
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
            questions = []
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

@pc.route('/login',methods=['POST'])
def loginDto():
    data = request.get_json()
    message = data.get('message')
    address = data.get('address')
    signature = data.get('signature')
    # 验证签名
    try:
        logging.info(f"message is {message}")
        logging.info(f"signature is {signature}")
        message_encoded = encode_defunct(text=message)
        recovered_address = Account.recover_message(signable_message=message_encoded, signature=signature)
        if recovered_address.lower() == address.lower():
        # 生成nonce并存入redis 过期时间为30s
            nonce = str(uuid.uuid4())
            try:
                redis_db = RedisManager()
                redis_db.insert_with_expiration(key=address,value=nonce)
                return jsonify({'success': True, 'nonce': nonce},200)
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}, 400)
        else:
            return jsonify({'success': False, 'message': 'Invalid signature'}, 401)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}, 400)


@pc.route('/verify',methods=['POST'])
def verifyNonce():
    data = request.get_json()
    nonce_user = data.get('nonce')
    address = data.get('address')
    # 从Redis获取nonce
    redis_db = RedisManager()
    nonce_redis = redis_db.get(address)
    tidb = TiDBManager()
    if nonce_redis==nonce_user:
        # 生成token 放在head中返回
        # 签名验证成功，生成JWT Token
        try:
            user_id = tidb.select_user_id(account=address)
            name = None
            if user_id is None:
                user_id = user_id[0]
                user_id = str(uuid.uuid4())
                tidb.upsert_user(user_id=user_id,account=address)
            else:
                res = tidb.select_user(user_id=user_id,name=True)
                if res:
                    name =  res[0]
            token = jwt.encode({  # user_id/ name / birthday
                'account': address,
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(days=7)  # Token 30分钟后过期
            }, os.environ['SECRET_KEY'], algorithm='HS256')
            response = make_response(jsonify({'success': True, 'message': 'login sucess','data':{'name':name,'account': address,'user_id': user_id,'token':f'Bearer {token}'}},200))
            return response
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}, 400)
    else:
        return jsonify({'success': False, 'error': 'Invalid nonce'}, 400)

@pc.route('/auth',methods=['GET'])
def auth():
    # 返回user_id 和 name
    auth_header = request.headers.get('Authorization')
    token_prefix, token = auth_header.split(" ")
    decoded_parameters = jwt.decode(token, os.environ['SECRET_KEY'], algorithms=["HS256"])
    tidb = TiDBManager()
    name = tidb.select_user(user_id=decoded_parameters['user_id'], name=True)[0]
    if name:
        return jsonify({"status": "success", "data":{'name':name[0],'user_id':decoded_parameters['user_id'],'account':decoded_parameters['account']}}, 200)
    else:
        return jsonify({"status": "database select Error"}, 500)

@pc.before_app_request
def before_request_for_blueprint():
    # 检查Authorization头是否存在
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        logging.info(f"Not the token user!")
        # response = make_response(jsonify({'message': 'Authorization header is missing!'}), 403)
        # return response
    else:
        # 检查Token是否以Bearer开头
        try:
            token_prefix, token = auth_header.split(" ")
            if token_prefix.lower() != 'bearer':
                raise ValueError
        except ValueError:
            response = make_response(jsonify({'message': 'Token is not properly formatted!'}), 403)
            return response

        # 验证Token
        try:
            jwt.decode(token, os.environ['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            response = make_response(jsonify({'message': 'Token has expired!'}), 403)
            return response
        except jwt.InvalidTokenError:
            response = make_response(jsonify({'message': 'Token is invalid!'}), 403)
            return response
