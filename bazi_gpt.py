import sxtwl
import argparse
import collections
import pprint
import datetime
from collections import OrderedDict
import openai
import os
import json

from lunar_python import Lunar
from colorama import init
from sizi import summarys
from sizi_gpt import summary
from bidict import bidict

Gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
Zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
shishen_shensha = {
    "正官": "政府、权力、规则、法律。正直、勤奋、克制、守信。女命丈夫、姻缘。",
    "七杀": "疾病、小人、贫穷、官非。多疑、冲动、好斗。女命情人。",
    "正印": "学历、证书、贵人、地位。善良、有爱心、有修养。母亲。",
    "偏印": "宗教、失业、学术、偏业。精明、警觉、创造力、孤独。继母。",
    "正财": "钱财、事业、富裕、健康。勤俭、专一、现实、敏感。男命妻子、姻缘。",
    "偏财": "财运、富裕、才艺、副业。豁达、交际、风流、拜金。男命情人、姻缘。",
    "食神": "平安、口福、才艺、智慧。宽容、人缘好、斯文、奉献。子女。",
    "伤官": "聪明、才华、技术、商业。悟性、张扬、创新、骄傲。克夫。",
    "比肩": "兄弟、公平、竞争、精力。毅力、勤奋、自尊、执行力。兄弟。",
    "劫财": "官非、贫困、破财、疾病。争斗、自我、冲动、直率。克妻。"
}
gan5 = {"甲":"木", "乙":"木", "丙":"火", "丁":"火", "戊":"土", "己":"土", 
        "庚":"金", "辛":"金", "壬":"水", "癸":"水"}
zhi5 = {
    "子":OrderedDict({"癸":8}), 
    "丑":OrderedDict({"己":5, "癸":2, "辛":1,}), 
    "寅":OrderedDict({"甲":5, "丙":2, "戊":1, }),
    "卯":OrderedDict({"乙":8}),
    "辰":OrderedDict({"戊":5, "乙":2, "癸":1, }),
    "巳":OrderedDict({ "丙":5, "戊":2, "庚":1,}),
    "午":OrderedDict({"丁":5, "己":3, }),
    "未":OrderedDict({"己":5, "丁":2, "乙":1,}),
    "申":OrderedDict({"庚":5, "壬":2, "戊":1, }),
    "酉":OrderedDict({"辛":8}),
    "戌":OrderedDict({"戊":5, "辛":2, "丁":1 }),
    "亥":OrderedDict({"壬":5, "甲":3, })}
ten_deities = {
    '甲':bidict({'甲':'比', "乙":'劫', "丙":'食', "丁":'伤', "戊":'才',
                  "己":'财', "庚":'杀', "辛":'官', "壬":'枭', "癸":'印', "子":'沐', 
                  "丑":'冠', "寅":'建', "卯":'帝', "辰":'衰', "巳":'病', "午":'死', 
                  "未":'墓', "申":'绝', "酉":'胎', "戌":'养', "亥":'长', '库':'未_', 
                  '本':'木', '克':'土', '被克':'金', '生我':'水', '生':'火','合':'己','冲':'庚'}),
    '乙':bidict({'甲':'劫', "乙":'比', "丙":'伤', "丁":'食', "戊":'财',
                  "己":'才', "庚":'官', "辛":'杀', "壬":'印',"癸":'枭', "子":'病', 
                  "丑":'衰', "寅":'帝', "卯":'建', "辰":'冠', "巳":'沐', "午":'长',
                  "未":'养', "申":'胎', "酉":'绝', "戌":'墓', "亥":'死', '库':'未_',
                  '本':'木', '克':'土', '被克':'金', '生我':'水', '生':'火','合':'庚','冲':'辛'}),
    '丙':bidict({'丙':'比', "丁":'劫', "戊":'食', "己":'伤', "庚":'才',
                  "辛":'财', "壬":'杀', "癸":'官', "甲":'枭', "乙":'印',"子":'胎', 
                  "丑":'养', "寅":'长', "卯":'沐', "辰":'冠', "巳":'建', "午":'帝',
                  "未":'衰', "申":'病', "酉":'死', "戌":'墓', "亥":'绝', '库':'戌_',
                  '本':'火', '克':'金', '被克':'水', '生我':'木', '生':'土','合':'辛','冲':'壬'}),
    '丁':bidict({'丙':'劫', "丁":'比', "戊":'伤', "己":'食', "庚":'财',
                  "辛":'才', "壬":'官', "癸":'杀', "甲":'印',"乙":'枭', "子":'绝', 
                  "丑":'墓', "寅":'死', "卯":'病', "辰":'衰', "巳":'帝', "午":'建',
                  "未":'冠', "申":'沐', "酉":'长', "戌":'养', "亥":'胎', '库':'戌_',
                  '本':'火', '克':'金', '被克':'水', '生我':'木', '生':'土','合':'壬','冲':'癸'}),
    '戊':bidict({'戊':'比', "己":'劫', "庚":'食', "辛":'伤', "壬":'才',
                  "癸":'财', "甲":'杀', "乙":'官', "丙":'枭', "丁":'印',"子":'胎', 
                  "丑":'养', "寅":'长', "卯":'沐', "辰":'冠', "巳":'建', "午":'帝',
                  "未":'衰', "申":'病', "酉":'死', "戌":'墓', "亥":'绝', '库':'辰_',
                  '本':'土', '克':'水', '被克':'木', '生我':'火', '生':'金','合':'癸','冲':''}),
    '己':bidict({'戊':'劫', "己":'比', "庚":'伤', "辛":'食', "壬":'财',
                  "癸":'才', "甲":'官', "乙":'杀', "丙":'印',"丁":'枭',"子":'绝', 
                  "丑":'墓', "寅":'死', "卯":'病', "辰":'衰', "巳":'帝', "午":'建',
                  "未":'冠', "申":'沐', "酉":'长', "戌":'养', "亥":'胎', '库':'辰_',
                  '本':'土', '克':'水', '被克':'木', '生我':'火', '生':'金','合':'甲','冲':''}),
    '庚':bidict({'庚':'比', "辛":'劫', "壬":'食', "癸":'伤', "甲":'才',
                  "乙":'财', "丙":'杀', "丁":'官', "戊":'枭', "己":'印',"子":'死', 
                  "丑":'墓', "寅":'绝', "卯":'胎', "辰":'养', "巳":'长', "午":'沐',
                  "未":'冠', "申":'建', "酉":'帝', "戌":'衰', "亥":'病', '库':'丑_',
                  '本':'金', '克':'木', '被克':'火', '生我':'土', '生':'水','合':'乙','冲':'甲'}), 
    '辛':bidict({'庚':'劫', "辛":'比', "壬":'伤', "癸":'食', "甲":'财',
                  "乙":'才', "丙":'官', "丁":'杀', "戊":'印', "己":'枭', "子":'长', 
                  "丑":'养', "寅":'胎', "卯":'绝', "辰":'墓', "巳":'死', "午":'病',
                  "未":'衰', "申":'帝', "酉":'建', "戌":'冠', "亥":'沐', '库':'丑_',
                  '本':'金', '克':'木', '被克':'火', '生我':'土', '生':'水','合':'丙','冲':'乙'}),
    '壬':bidict({'壬':'比', "癸":'劫', "甲":'食', "乙":'伤', "丙":'才',
                  "丁":'财', "戊":'杀', "己":'官', "庚":'枭', "辛":'印',"子":'帝', 
                  "丑":'衰', "寅":'病', "卯":'死', "辰":'墓', "巳":'绝', "午":'胎',
                  "未":'养', "申":'长', "酉":'沐', "戌":'冠', "亥":'建', '库':'辰_',
                  '本':'水', '克':'火', '被克':'土', '生我':'金', '生':'木','合':'丁','冲':'丙'}),
    '癸':bidict({'壬':'劫', "癸":'比', "甲":'伤', "乙":'食', "丙":'财',
                  "丁":'才', "戊":'官', "己":'杀', "庚":'印',"辛":'枭', "子":'建', 
                  "丑":'冠', "寅":'沐', "卯":'长', "辰":'养', "巳":'胎', "午":'绝',
                  "未":'墓', "申":'死', "酉":'病', "戌":'衰', "亥":'帝', '库':'辰_',
                  '本':'水', '克':'火', '被克':'土', '生我':'金', '生':'木','合':'戊','冲':'丁'}), 

}

zhi_atts = {
    "子":{"冲":"午", "刑":"卯", "被刑":"卯", "合":("申","辰"), "会":("亥","丑"), '害':'未', '破':'酉', "六":"丑","暗":"",},
    "丑":{"冲":"未", "刑":"戌", "被刑":"未", "合":("巳","酉"), "会":("子","亥"), '害':'午', '破':'辰', "六":"子","暗":"寅",},
    "寅":{"冲":"申", "刑":"巳", "被刑":"申", "合":("午","戌"), "会":("卯","辰"), '害':'巳', '破':'亥', "六":"亥","暗":"丑",},
    "卯":{"冲":"酉", "刑":"子", "被刑":"子", "合":("未","亥"), "会":("寅","辰"), '害':'辰', '破':'午', "六":"戌","暗":"申",},
    "辰":{"冲":"戌", "刑":"辰", "被刑":"辰", "合":("子","申"), "会":("寅","卯"), '害':'卯', '破':'丑', "六":"酉","暗":"",},
    "巳":{"冲":"亥", "刑":"申", "被刑":"寅", "合":("酉","丑"), "会":("午","未"), '害':'寅', '破':'申', "六":"申","暗":"",},
    "午":{"冲":"子", "刑":"午", "被刑":"午", "合":("寅","戌"), "会":("巳","未"), '害':'丑', '破':'卯', "六":"未","暗":"亥",},
    "未":{"冲":"丑", "刑":"丑", "被刑":"戌", "合":("卯","亥"), "会":("巳","午"), '害':'子', '破':'戌', "六":"午","暗":"",},
    "申":{"冲":"寅", "刑":"寅", "被刑":"巳", "合":("子","辰"), "会":("酉","戌"), '害':'亥', '破':'巳', "六":"巳","暗":"卯",},
    "酉":{"冲":"卯", "刑":"酉", "被刑":"酉", "合":("巳","丑"), "会":("申","戌"), '害':'戌', '破':'子', "六":"辰","暗":"",},
    "戌":{"冲":"辰", "刑":"未", "被刑":"丑", "合":("午","寅"), "会":("申","酉"), '害':'酉', '破':'未', "六":"卯","暗":"",},
    "亥":{"冲":"巳", "刑":"亥", "被刑":"亥", "合":("卯","未"), "会":("子","丑"), '害':'申', '破':'寅', "六":"寅","暗":"午",},
}

empties = {
    ('甲', '子'): ('戌','亥'), ('乙', '丑'):('戌','亥'), 
    ('丙', '寅'): ('戌','亥'), ('丁', '卯'): ('戌','亥'), 
    ('戊', '辰'): ('戌','亥'), ('己', '巳'): ('戌','亥'),
    ('庚', '午'): ('戌','亥'), ('辛', '未'): ('戌','亥'),
    ('壬', '申'): ('戌','亥'), ('癸', '酉'): ('戌','亥'),

    ('甲', '戌'): ('申','酉'), ('乙', '亥'): ('申','酉'),
    ('丙', '子'): ('申','酉'), ('丁', '丑'): ('申','酉'),
    ('戊', '寅'): ('申','酉'), ('己', '卯'): ('申','酉'),
    ('庚', '辰'):('申','酉'), ('辛', '巳'): ('申','酉'),
    ('壬', '午'): ('申','酉'), ('癸', '未'): ('申','酉'),

    ('甲', '申'): ('午','未'), ('乙', '酉'): ('午','未'),
    ('丙', '戌'): ('午','未'), ('丁', '亥'): ('午','未'),
    ('戊', '子'): ('午','未'), ('己', '丑'): ('午','未'), 
    ('庚', '寅'): ('午','未'), ('辛', '卯'): ('午','未'),
    ('壬', '辰'): ('午','未'), ('癸', '巳'): ('午','未'),

    ('甲', '午'): ('辰','己'), ('乙', '未'): ('辰','己'),
    ('丙', '申'): ('辰','己'), ('丁', '酉'): ('辰','己'),
    ('戊', '戌'): ('辰','己'), ('己', '亥'): ('辰','己'),
    ('庚', '子'): ('辰','己'), ('辛', '丑'): ('辰','己'),
    ('壬', '寅'): ('辰','己'), ('癸', '卯'): ('辰','己'),

    ('甲', '辰'): ('寅','卯'), ('乙', '巳'): ('寅','卯'),
    ('丙', '午'): ('寅','卯'), ('丁', '未'): ('寅','卯'),
    ('戊', '申'): ('寅','卯'), ('己', '酉'): ('寅','卯'),
    ('庚', '戌'): ('寅','卯'), ('辛', '亥'): ('寅','卯'),
    ('壬', '子'): ('寅','卯'), ('癸', '丑'): ('寅','卯'), 


    ('甲', '寅'): ('子','丑'), ('乙', '卯'): ('子','丑'),     
    ('丙', '辰'): ('子','丑'), ('丁', '巳'): ('子','丑'), 
    ('戊', '午'): ('子','丑'), ('己', '未'): ('子','丑'),
    ('庚', '申'): ('子','丑'), ('辛', '酉'): ('子','丑'), 
    ('壬', '戌'): ('子','丑'), ('癸', '亥'): ('子','丑'),    
}
year_shens = {
    '孤辰':{"子":"寅", "丑":"寅", "寅":"巳", "卯":"巳", "辰":"巳", "巳":"申", 
              "午":"申", "未":"申", "申":"亥", "酉":"亥", "戌":"亥", "亥":"寅"},
    '寡宿':{"子":"戌", "丑":"戌", "寅":"丑", "卯":"丑", "辰":"丑", "巳":"辰", 
              "午":"辰", "未":"辰", "申":"未", "酉":"未", "戌":"未", "亥":"戌"},   
    '大耗':{"子":"巳未", "丑":"午申", "寅":"未酉", "卯":"申戌", "辰":"酉亥", "巳":"戌子", 
              "午":"亥丑", "未":"子寅", "申":"丑卯", "酉":"寅辰", "戌":"卯巳", "亥":"辰午"},      
}

month_shens = {
    '天德':{"子":"巳", "丑":"庚", "寅":"丁", "卯":"申", "辰":"壬", "巳":"辛", 
            "午":"亥", "未":"甲", "申":"癸", "酉":"寅", "戌":"丙", "亥":"乙"},
    '月德':{"子":"壬", "丑":"庚", "寅":"丙", "卯":"甲", "辰":"壬", "巳":"庚", 
              "午":"丙", "未":"甲", "申":"壬", "酉":"庚", "戌":"丙", "亥":"甲"},
}
    

day_shens = { 
    '将星':{"子":"子", "丑":"酉", "寅":"午", "卯":"卯", "辰":"子", "巳":"酉", 
              "午":"午", "未":"卯", "申":"子", "酉":"酉", "戌":"午", "亥":"卯"},      
    '华盖':{"子":"辰", "丑":"丑", "寅":"戌", "卯":"未", "辰":"辰", "巳":"丑", 
              "午":"戌", "未":"未", "申":"辰", "酉":"丑", "戌":"戌", "亥":"未"}, 
    '驿马': {"子":"寅", "丑":"亥", "寅":"申", "卯":"巳", "辰":"寅", "巳":"亥", 
            "午":"申", "未":"巳", "申":"寅", "酉":"亥", "戌":"申", "亥":"巳"},
    '劫煞': {"子":"巳", "丑":"寅", "寅":"亥", "卯":"申", "辰":"巳", "巳":"寅", 
         "午":"亥", "未":"申", "申":"巳", "酉":"寅", "戌":"亥", "亥":"申"},
    '亡神': {"子":"亥", "丑":"申", "寅":"巳", "卯":"寅", "辰":"亥", "巳":"申", 
            "午":"巳", "未":"寅", "申":"亥", "酉":"申", "戌":"巳", "亥":"寅"},    
    '桃花': {"子":"酉", "丑":"午", "寅":"卯", "卯":"子", "辰":"酉", "巳":"午", 
            "午":"卯", "未":"子", "申":"酉", "酉":"午", "戌":"卯", "亥":"子"},        
}
g_shens = {
    '天乙':{"甲":'未丑',  "乙":"申子", "丙":"酉亥", "丁":"酉亥", "戊":'未丑', "己":"申子", 
            "庚": "未丑", "辛":"寅午", "壬": "卯巳", "癸":"卯巳"},
    '文昌':{"甲":'巳', "乙":"午", "丙":"申", "丁":"酉", "戊":"申", "己":"酉", 
            "庚": "亥", "辛":"子", "壬": "寅", "癸":"丑"},   
    '阳刃':{"甲":'卯', "乙":"", "丙":"午", "丁":"", "戊":"午", "己":"", 
            "庚": "酉", "辛":"", "壬": "子", "癸":""},     
    '红艳':{"甲":'午', "乙":"午", "丙":"寅", "丁":"未", "戊":"辰", "己":"辰", 
            "庚": "戌", "辛":"酉", "壬": "子", "癸":"申"},       
}
def shishenGPT(shishen):
    prompt = f"""
    你是个算命大师，我现在会把某个人的十神告诉你，十神对应的含义是:

    正官：政府、权力、规则、法律。正直、勤奋、克制、守信。女命丈夫、姻缘。
    七杀：疾病、小人、贫穷、官非。多疑、冲动、好斗。女命情人。
    正印：学历、证书、贵人、地位。善良、有爱心、有修养。母亲。
    偏印：宗教、失业、学术、偏业。精明、警觉、创造力、孤独。继母。
    正财：钱财、事业、富裕、健康。勤俭、专一、现实、敏感。男命妻子、姻缘。
    偏财：财运、富裕、才艺、副业。豁达、交际、风流、拜金。男命情人、姻缘。
    食神：平安、口福、才艺、智慧。宽容、人缘好、斯文、奉献。子女。
    伤官：聪明、才华、技术、商业。悟性、张扬、创新、骄傲。克夫。
    比肩：兄弟、公平、竞争、精力。毅力、勤奋、自尊、执行力。兄弟。
    劫财：官非、贫困、破财、疾病。争斗、自我、冲动、直率。克妻。

    请根据我发的十神找到对应的解释，然后根据这些解释给出此人命理的详细分析，返回的答案不能出现十神的解释
    注意返回在200字以上
    """
    messages = [{"role":"system","content":prompt}]    
    messages.append({"role": "user","content":f"十神为：{shishen}"})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=messages
    )
    string_res = completion["choices"][0]["message"]["content"].strip()
    return string_res

def mingyunGPT(bazi,mingyun):
    prompt = f"""
    你是个算命大师，我现在会把某个人的八字和命理告诉你
    请根据我发的八字和命理给出到对应的命运描述，并帮我组织下语言发我白话文，注意不要出现'根据你提供xxx'
    注意返回在200字以上
    """
    messages = [{"role": "system", "content": prompt}]
    messages.append({"role": "user","content": f"八字为：{bazi} \n\n 命运为：{mingyun}"})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=messages
    )
    string_res = completion["choices"][0]["message"]["content"].strip()
    return string_res

def chushenGPT(bazi):
    prompt = f"""
    你是个算命大师，我现在会把某个人的八字告诉你
    请根据我发的八字，测算这个人的出身情况
    注意返回在200字以上
    """
    messages = [{"role": "system", "content": prompt}]
    messages.append({"role": "user","content": f"八字为：{bazi} \n\n"})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=messages
    )
    string_res = completion["choices"][0]["message"]["content"].strip()
    return string_res
import io
import os

import sys
def capture_print(func):
    def wrapper(*args, **kwargs):
        captured_output = io.StringIO()
        current_stdout = sys.stdout
        try:
            sys.stdout = captured_output
            func(*args, **kwargs)
            return captured_output.getvalue()
        finally:
            sys.stdout = current_stdout
    return wrapper


@capture_print
def bazipaipan(year, month, day, time, gender):
    def check_gan(gan, gans):
        result = ''
        if ten_deities[gan]['合'] in gans:
            result += "合" + ten_deities[gan]['合']
        if ten_deities[gan]['冲'] in gans:
            result += "冲" + ten_deities[gan]['冲']
        return result
    def yinyang(item):
        if item in Gan:
            return '＋' if Gan.index(item)%2 == 0 else '－'
        else:
            return '＋' if Zhi.index(item)%2 == 0 else '－'
    def get_shens(gans, zhis, gan_, zhi_):
        
        all_shens = []
        for item in year_shens:
            if zhi_ in year_shens[item][zhis.year]:    
                all_shens.append(item)
                    
        for item in month_shens:
            if gan_ in month_shens[item][zhis.month] or zhi_ in month_shens[item][zhis.month]:     
                all_shens.append(item)
                    
        for item in day_shens:
            if zhi_ in day_shens[item][zhis.day]:     
                all_shens.append(item)
                    
        for item in g_shens:
            if zhi_ in g_shens[item][mingzhu]:    
                all_shens.append(item) 
        if all_shens:  
            return "  神:" + ' '.join(all_shens)
        else:
            return ""
    sex = '女' if gender else '男' # 1 为男，0 为女
    print("性别：{}".format(sex))
    day_lunar = sxtwl.fromSolar(int(year), int(month), int(day))
    print("公历:", end='')
    print("{}年{}月{}日".format(day_lunar.getSolarYear(), day_lunar.getSolarMonth(), day_lunar.getSolarDay()))
    lunar_birthday = day_lunar.getLunarYear() # 农历
    print("农历:", end='')
    Lleap = "闰" if day_lunar.isLunarLeap() else ""
    print("{}年{}{}月{}日".format(day_lunar.getLunarYear(), Lleap, day_lunar.getLunarMonth(), day_lunar.getLunarDay()))
    lunar = Lunar.fromYmdHms(day_lunar.getLunarYear(), day_lunar.getLunarMonth(), day_lunar.getLunarDay(),int(time), 0, 0)
    eightWord = lunar.getEightChar() # 八字
    print("八字：{}".format(eightWord))

    gz = day_lunar.getHourGZ(int(time))
    yTG = day_lunar.getYearGZ()
    mTG = day_lunar.getMonthGZ()
    dTG  = day_lunar.getDayGZ()
    Gans = collections.namedtuple("Gans", "year month day time")
    Zhis = collections.namedtuple("Zhis", "year month day time")
    gans = Gans(year=Gan[yTG.tg], month=Gan[mTG.tg], 
                day=Gan[dTG.tg], time=Gan[gz.tg])
    zhis = Zhis(year=Zhi[yTG.dz], month=Zhi[mTG.dz], 
                day=Zhi[dTG.dz], time=Zhi[gz.dz])
    mingzhu = gans.day
    print(f"命主: {mingzhu}")

    tianganshishen = lunar.getBaZiShiShenGan()
    dizhishishen = lunar.getBaZiShiShenZhi()
    nianshishen = lunar.getBaZiShiShenYearZhi()
    yueshishen = lunar.getBaZiShiShenMonthZhi()
    rishishen = lunar.getBaZiShiShenDayZhi()
    shishishen = lunar.getBaZiShiShenTimeZhi()
    shishen = [tianganshishen[0], tianganshishen[1], tianganshishen[3]]
    shishen.extend(nianshishen)
    shishen.extend(yueshishen)
    shishen.extend(rishishen)
    shishen.extend(shishishen)
    print("十神:", end='')
    print('\t'.join(shishen))
    print("十神神煞:")
    for ss in shishen:
        print(f"\t{ss}:{shishen_shensha[ss]}")
    wuXing = lunar.getBaZiWuXing()  # 五行
    print("五行:", end='')
    print('\t'.join(wuXing))
    scores = {"金":0, "木":0, "水":0, "火":0, "土":0} # 五行分数
    for item in gans:  
        scores[gan5[item]] += 5

    for item in list(zhis) + [zhis.month]:  
        for gan in zhi5[item]:
            scores[gan5[gan]] += zhi5[item][gan]
    print(f"五行分数: {scores}")
    # Find the minimum score
    min_score = min(scores.values())
    # Get the key(s) with the minimum score
    min_score_keys = [k for k, v in scores.items() if v == min_score]
    zero_score_keys = [k for k, v in scores.items() if v == 0]
    if zero_score_keys:
        print(f"五行元素中绝对缺失的有: {zero_score_keys}")
    print(f"五行元素中相对缺失的有: {min_score_keys}")

    print("十神分析:\n")
    print(shishenGPT(shishen))
    print("命分析:\n")
    zhus = [item for item in zip(gans, zhis)]
    sum_index = ''.join([mingzhu, '日', *zhus[3]])
    print(sum_index)
    print(summary[sum_index])
    print(mingyunGPT(eightWord,summary[sum_index]))

    print("大运分析：\n")
    dayuns = []
    # 计算大运
    seq = Gan.index(gans.year)
    if gender:
        if seq % 2 == 0:
            direction = 1
        else:
            direction = -1
    else:
        if seq % 2 == 0:
            direction = -1
        else:
            direction = 1
    gan_seq = Gan.index(gans.month)
    zhi_seq = Zhi.index(zhis.month)
    for i in range(12):
        gan_seq += direction
        zhi_seq += direction
        dayuns.append(Gan[gan_seq%10] + Zhi[zhi_seq%12])
    birthday = datetime.date(day_lunar.getSolarYear(), day_lunar.getSolarMonth(), day_lunar.getSolarDay()) 
    count = 0
    for i in range(30):    
        #print(birthday)
        day_ = sxtwl.fromSolar(birthday.year, birthday.month, birthday.day)
        #if day_.hasJieQi() and day_.getJieQiJD() % 2 == 1
        if day_.hasJieQi() and day_.getJieQi() % 2 == 1:
                break
            #break        
        birthday += datetime.timedelta(days=direction)
        count += 1
    ages = [(round(count/3 + 10*i), round(int(year) + 10*i + count//3)) for i in range(8)]
    
    for (seq, value) in enumerate(ages):
        gan_ = dayuns[seq][0]
        zhi_ = dayuns[seq][1]
        fu = '*' if (gan_, zhi_) in zhus else " "
        zhi5_ = ''
        for gan in zhi5[zhi_]:
            zhi5_ = zhi5_ + "{}{}{}　".format(gan, gan5[gan], ten_deities[mingzhu][gan]) 
        
        zhi__ = set() # 大运地支关系
        
        for item in zhis:
            for type_ in zhi_atts[zhi_]:
                if item in zhi_atts[zhi_][type_]:
                    zhi__.add(type_ + ":" + item)
        zhi__ = '  '.join(zhi__)
        
        empty = chr(12288)
        if zhi_ in empties[zhus[2]]:
            empty = '空'        
        
        jia = ""
        if gan_ in gans:
            for i in range(4):
                if gan_ == gans[i]:
                    if abs(Zhi.index(zhi_) - Zhi.index(zhis[i])) == 2:
                        jia = jia + "  --夹：" +  Zhi[( Zhi.index(zhi_) + Zhi.index(zhis[i]) )//2]
                    if abs( Zhi.index(zhi_) - Zhi.index(zhis[i]) ) == 10:
                        jia = jia + "  --夹：" +  Zhi[(Zhi.index(zhi_) + Zhi.index(zhis[i]))%12]
                
        out = "{1:<4d}{2:<5s}{3} {15} {14} {13}  {4}:{5}{8}{6:{0}<6s}{12}{7}{8}{9} {10:{0}<15s} {11}".format(
            chr(12288), int(value[0]), '', dayuns[seq],ten_deities[mingzhu][gan_], gan_,check_gan(gan_, gans), 
            zhi_, yinyang(zhi_), '', zhi5_, zhi__,empty, fu, '', '') 
        gan_index = Gan.index(gan_)
        zhi_index = Zhi.index(zhi_)
        out = out + jia + get_shens(gans, zhis, gan_, zhi_)
        print(out)

    print("出身分析：\n")
    print(chushenGPT(eightWord))
# if __name__ =="__main__":
#     year = '1991'
#     month = '7'
#     day = '25'
#     time = '10'

#     bazipaipan(year,month,day,time,True)

