import sxtwl
import json
import os
import time
from flask import Flask, Response, request, stream_with_context, jsonify, make_response
from datetime import datetime, timedelta
import uuid
import logging

from chat.tg_bot import tg_bot_ChatGPT_assistant
from database.mysql_db import TiDBManager
from database.redis_db import RedisManager
from bazi_info.bazi import baziAnalysis
from bazi_info.bazi_match import baziMatch
from bazi_info.bazi_gpt import bazipaipan
from utils.options_class import options
from utils.util import *
from utils.question_rec import rec_question
from flask import Blueprint
tg_bot = Blueprint('tg_bot', __name__)


@tg_bot.route('/first_visit',methods=['POST'])
def tg_bot_first_visit():
    if request.method =="POST":
        data = request.get_json()
        conversation_id = data['conversation_id']
        tidb_manager = TiDBManager()
        res = tidb_manager.select_user(user_id==conversation_id, name=True)
        if res:
            return jsonify({"status": "success, not first time.", "data": 0,"status_code":200})
        else:
            return jsonify({"status": "error, it is first time.", "data": 1,"status_code":200})

@tg_bot.route('/get_matcher',methods=['POST'])
def tg_bot_get_matcher():
    if request.method =="POST":
        data = request.get_json()
        user_id = data['user_id']
        matcher_type = data['matcher_type']
        tidb_manager = TiDBManager()
        if matcher_type==1:
            res = tidb_manager.select_matcherPerson(user_id)
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

@tg_bot.route('/chat', methods=['POST'])
def tg_bot_chat():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    lang = data.get('lang')
    chat = tg_bot_ChatGPT_assistant(conversation_id, lang=lang, matcher_type=0,message=user_message)
    logging.info(f"conversation_id {conversation_id}, message {user_message}")
    # Initialize or retrieve existing ChatGPT instance for the user
    return Response(chat.ask_gpt_stream(user_message), mimetype="text/event-stream")


@tg_bot.route('/bazi_insert', methods=['POST'])
def tg_bot_bazi_insert():
    data = request.get_json()
    birthday = data.get('birthday') # 格式：2000-5-5-10
    conversation_id = data.get('conversation_id')
    matcher_type = data.get('matcher_type')
    gender = data.get("gender")
    name = data.get("name")
    user_id = data.get('user_id')
    matcher_id = data.get('matcher_id')
    lang = data.get('lang')

    tidb_manager = TiDBManager()
    # 如果matcher_type 是0代表本人，是1，代表其他人， 2代表资产(int)
    if matcher_type == 0:
        # 插入自己八字
        year, month, day, time = map(int, birthday.split('-'))
        op = options(year=year,month=month,day=day,time=time,n=gender)
        birthday = datetime(year, month, day, time)
        (mingyun_analysis,chushen_analysis),bazi_info_gpt = bazipaipan(year,month,day,time,gender,name=name,tg_bot=True)
        bazi_info = baziAnalysis(op,mingyun_analysis,chushen_analysis)
        first_reply = "您好，欢迎使用AI算命。\n" + bazi_info_gpt.split("---------------")[0]
        bazi_id = tidb_manager.select_bazi_id(conversation_id=conversation_id)
        tidb_manager = TiDBManager()
        # 如果存在，那就将之前的置为 is_delete 置为1
        if bazi_id:
            tidb_manager.update_reset_delete(bazi_id=bazi_id)
        bazi_id = tidb_manager.insert_bazi_chat(user_id, conversation_id, bazi_info, bazi_info_gpt, first_reply)
        tidb_manager.upsert_user(user_id, birthday=birthday, name=name, gender=gender) # gender 0 为男，1 为女
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
        # 如果需要翻译成英文
        if lang=="En":
            result_text = translate(first_reply)
        else:
            result_text = first_reply
        return Response(stream_output(None,user_id,result_text), mimetype="text/event-stream")

    elif matcher_type == 1:
        birthday_user = tidb_manager.select_user(user_id,birthday=True)
        year_match, month_match, day_match, time_match = map(int, birthday.split('-'))
        if matcher_id:
            birthday_match = tidb_manager.select_matcherPerson(user_id,id=matcher_id)
            year_match,month_match,day_match,time_match = birthday_match.year,birthday_match.month,birthday_match.day,birthday_match.hour
        else:
            birthday_match = datetime(year_match, month_match, day_match, time_match)
            matcher_id = str(uuid.uuid4())
            tidb_manager.upsert_matcherPerson(matcher_id, gender, birthday, user_id, name=name)

        res_match = baziMatch(birthday_user.year,birthday_user.month,birthday_user.day,birthday_user.hour, year_match,month_match,day_match,time_match)
        op = options(year=year_match,month=month_match,day=day_match,time=time_match,n=gender)
        (mingyun_analysis,chushen_analysis),bazi_info_gpt = bazipaipan(year_match,month_match,day_match,time_match,gender,name=name,tg_bot=True)
        bazi_info = baziAnalysis(op,mingyun_analysis,chushen_analysis)
        head = f"他人/配对者/配对人, {name}的八字背景信息如下:\n"
        db_res = head + bazi_info + "\n" + res_match
        db_res_gpt = head + bazi_info_gpt + "\n" + res_match
        first_reply = "您好，欢迎使用AI算命。\n" + bazi_info_gpt.split("---------------")[0]
        bazi_id = tidb_manager.insert_bazi_chat(user_id, conversation_id, db_res, db_res_gpt, first_reply, matcher_id=matcher_id, matcher_type=matcher_type)
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

@tg_bot.route('/reset_chat',methods=['POST'])
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
            bazi_id = tidb_manager.select_bazi_id(conversation_id=conversation_id)
            logging.info(bazi_id)
            first_reply = tidb_manager.select_chat_bazi(bazi_id=bazi_id, first_reply=True)[0]
            logging.info(first_reply)
        # 重置当前对话 其他人
        else:
            bazi_id = tidb_manager.select_bazi_id(conversation_id=conversation_id,matcher_id=matcher_id)
            first_reply = tidb_manager.select_chat_bazi(bazi_id=bazi_id, first_reply=True)[0]
        if matcher_type==2:
            if bazi_info ==False or bazi_id ==False:
                birthday_match = tidb_manager.select_birthday(matcher_type=2,matcher_id=matcher_id)
                year_match,month_match,day_match,time_match = birthday_match.year,birthday_match.month,birthday_match.day,birthday_match.hour
                birthday_user = tidb_manager.select_birthday(user_id)
                res = baziMatch(birthday_user.year,birthday_user.month,birthday_user.day,birthday_user.hour, year_match,month_match,day_match,time_match,name=name)
                bazi_id = tidb_manager.insert_baziInfo(user_id, birthday_user,res, res, conversation_id, birthday_match=birthday_match, matcher_type=matcher_type, matcher_id=matcher_id,first_reply=res)
                tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
                return Response(stream_output(None, None, res), mimetype="text/event-stream")
        tidb_manager.insert_tg_bot_conversation_user(conversation_id, user_id, bazi_id)
        # 如果需要翻译成英文
        if lang=="En":
            result_text = translate(first_reply)
        else:
            result_text = first_reply
        logging.info("result_text")
        return Response(stream_output(None, None, result_text), mimetype="text/event-stream")