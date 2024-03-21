import sxtwl
import argparse
import collections
import pprint
import datetime
from collections import OrderedDict
import openai
import os
import json
from openai import OpenAI
from lunar_python import Lunar
from colorama import init
from bazi_info.sizi import summarys
from bazi_info.sizi_gpt import summary
from bidict import bidict

client = OpenAI()
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
sx_xingge = {
    '鼠':"做事态度积极，勤奋努力，头脑机智手脚灵巧；待人和蔼，有自我约束力，遇事能替人着想；适应性强，善于结交各方面的朋友；多情善感，性格稍微内向，行动上活泼，待人热情；观察细致，思维方式有条理；稍微胆小怕事，多疑保守，个别问题上约显目光短浅，认识深度不够。",
    '牛':"""勤奋努力，有强烈的进取心；忠厚老实，务实，责任心强，有耐力；有正义感，爱打抱不平；勤俭持家，稳定；稍微固执已见，缺乏通融； 有时钻"牛角尖"主观独断。""",
    '虎':"""有朝气，有雄心壮志；敢想敢干，勇于开拓；热情大方，顽强自信，刚愎自用；有正义感，乐于助人；易动感情，自以为是，稍微有点孤傲任性。""",
    '兔':"温柔、善良、乐观，感情细腻；精明灵活，体谅他人；气质高雅，思维细腻；能忍耐谦让，不好争执；约有虚荣心，性情有时候不稳定，容易急躁，满足于现状的时候多。",
    '龙':"勇往直前，有旺盛的进取心；专心致志，果断肯干；孝顺，慷慨，善于理财；聪明，有才能，气度高；有时容易急躁，盛气凌人，主观固执，约显争强好胜，不服输。",
    '蛇':"""专心致志，认真负责；心灵手巧，思路敏捷；精力充沛，随和开朗；表面沉着，有时口快；有时动摇不定，心胸狭窄，有时钻"牛角尖"，性情多疑，不太信任他人。""",
    '马':"精力旺盛，刚毅果断；善恶分明，耿直热情；能言善辩，不怕困难，勇往直前；欠缺冷静有时急躁，个性约为倔强。",
    '羊':"研究欲强，富有创造性；善良、宽容、顺从；有耐心，不惹是非，适应环境快；易动感情，主观性差，随波逐流优柔寡断。",
    '猴':"有进取心，喜欢竞争；多才多艺，多面手；略有虚荣心，生活浪漫，不受拘束；能与人融洽相处，善于应酬；有嫉妒心，轻浮散漫，性情多变，约缺诚信。",
    '鸡':"精力充沛，善于言谈；调查研究，讲究效率；果断、敏锐、好表现自己；勇往直前，心强好胜，总想一鸣惊人；脾气古怪，爱争善辩，固执已见，稍微自私。",
    '狗':"意志坚定，忠实可靠；正义、公平、敏捷；聪明、有见识，有条理；受人所用，能听话吃苦，注重现实；有时急躁，有盲目倾向，顽固，不计后果，防止被人因小利而亡大义。",
    '猪':"真挚、诚实、有同情心；精力旺盛，待人诚实；专心致志，凡事热心；信任别人，开朗乐观；易动感情，固执保守，目光短浅，有时脾气不稳。" 
}

nayins = {
    ('甲', '子'): '海中金', ('乙', '丑'): '海中金', ('壬', '寅'): '金泊金', ('癸', '卯'): '金泊金',
    ('庚', '辰'): '白蜡金', ('辛', '巳'): '白蜡金', ('甲', '午'): '砂中金', ('乙', '未'): '砂中金',
    ('壬', '申'): '剑锋金', ('癸', '酉'): '剑锋金', ('庚', '戌'): '钗钏金', ('辛', '亥'): '钗钏金',
    ('戊', '子'): '霹雳火', ('己', '丑'): '霹雳火', ('丙', '寅'): '炉中火', ('丁', '卯'): '炉中火',
    ('甲', '辰'): '覆灯火', ('乙', '巳'): '覆灯火', ('戊', '午'): '天上火', ('己', '未'): '天上火',
    ('丙', '申'): '山下火', ('丁', '酉'): '山下火', ('甲', '戌'): '山头火', ('乙', '亥'): '山头火',
    ('壬', '子'): '桑柘木', ('癸', '丑'): '桑柘木', ('庚', '寅'): '松柏木', ('辛', '卯'): '松柏木',
    ('戊', '辰'): '大林木', ('己', '巳'): '大林木', ('壬', '午'): '杨柳木', ('癸', '未'): '杨柳木',
    ('庚', '申'): '石榴木', ('辛', '酉'): '石榴木', ('戊', '戌'): '平地木', ('己', '亥'): '平地木',
    ('庚', '子'): '壁上土', ('辛', '丑'): '壁上土', ('戊', '寅'): '城头土', ('己', '卯'): '城头土',
    ('丙', '辰'): '砂中土', ('丁', '巳'): '砂中土', ('庚', '午'): '路旁土', ('辛', '未'): '路旁土',
    ('戊', '申'): '大驿土', ('己', '酉'): '大驿土', ('丙', '戌'): '屋上土', ('丁', '亥'): '屋上土',
    ('丙', '子'): '涧下水', ('丁', '丑'): '涧下水', ('甲', '寅'): '大溪水', ('乙', '卯'): '大溪水',
    ('壬', '辰'): '长流水', ('癸', '巳'): '长流水', ('丙', '午'): '天河水', ('丁', '未'): '天河水',
    ('甲', '申'): '井泉水', ('乙', '酉'): '井泉水', ('壬', '戌'): '大海水', ('癸', '亥'): '大海水',    
}
gong_he = {"申辰": '子', "巳丑": '酉', "寅戌": '午', "亥未": '卯',
           "辰申": '子', "丑巳": '酉', "戌寅": '午', "未亥": '卯',}
def remove_brackets_content(sentence):
    import re
    # 使用正则表达式匹配"【】"及其内部的内容，并将其替换为空
    new_sentence = re.sub(r'【.*?】', '', sentence)
    return new_sentence

def get_second_bracket_value(s):
    # 找到第一个左花括号的索引
    start_index = s.find('{') + 1
    # 找到第一个右花括号的索引
    end_index = s.find('}')
    # 找到第二个左花括号的索引
    second_start_index = s.find('{', end_index) + 1
    # 找到第二个右花括号的索引
    second_end_index = s.find('}', second_start_index)
    # 返回第二对花括号中的内容
    return s[second_start_index:second_end_index]

def shishenGPT(shishen,sex):
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
    注意返回在100-150字
    注意此人的性别是{sex}
    回答时，如果性别是女，用她。性别是男，用他。
    用json的格式返回. 格式为 {{”response“:十神分析解释}}
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
        messages=[{"role": "system", "content": prompt},
                {"role": "user", "content":f"十神为：{shishen}"}],
        max_tokens = 2048,
        temperature = 0,
        response_format={"type": "json_object"}

    )
    string_res = completion.choices[0].message.content.strip()
    string_res = json.loads(string_res)

    return string_res["response"]

def xinggeGPT(bazi,shishen,wuxing,sex):
    prompt = f"""
    你是个算命大师负主要负责个人性格推理分析。我现在会把八字、五行、十神告诉你，你需要结合八字、五行、十神推测出此人的性格。
    不要出现五行的分析情况
    不要出现"xx相生相克"的分析情况
    不要出现'根据八字、五行和十神的信息分析'等字眼
    注意返回在100-150字
    注意此人的性别是{sex}
    回答时，如果性别是女，用她。性别是男，用他。
    用json的格式返回. 格式为 {{”response“:性格分析}}
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
        messages=[{"role": "system", "content": prompt},
                {"role": "user", "content":f"八字为:{bazi}\n\n五行为:{wuxing}\n\n十神为：{shishen}"}],
        max_tokens = 2048,
        temperature = 0,
        response_format={"type": "json_object"}

    )
    string_res = completion.choices[0].message.content.strip()
    string_res = json.loads(string_res)

    return string_res["response"]

def caiyunGPT(bazi,shishen,wuxing,sex):
    prompt = f"""
    你是个算命大师负主要负责个人财运分析。我现在会把八字、五行、十神告诉你，你需要结合八字、五行、十神推测出此人的财运情况。
    不要出现五行的分析情况
    不要出现"xx相生相克"的分析情况
    不要出现'根据八字、五行和十神的信息分析'等字眼
    注意返回在100-150字
    注意此人的性别是{sex}
    回答时，如果性别是女，用她。性别是男，用他。
    用json的格式返回. 格式为 {{”response“:财运分析情况}}
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
        messages=[{"role": "system", "content": prompt},
                {"role": "user", "content":f"八字为:{bazi}\n\n五行为:{wuxing}\n\n十神为：{shishen}"}],
        max_tokens = 2048,
        temperature = 0,
        response_format={"type": "json_object"}

    )
    string_res = completion.choices[0].message.content.strip()
    string_res = json.loads(string_res)

    return string_res["response"]

def yinyuanGPT(bazi,shishen,wuxing,sex):
    prompt = f"""
    你是个算命大师负主要负责个人姻缘情况分析。我现在会把八字、五行、十神告诉你，你需要结合八字、五行、十神推测出此人的姻缘情况。
    不要出现'根据八字和十神的信息分析'等字眼
    不要出现五行的分析情况
    不要出现"xx相生相克"的分析情况
    注意此人的性别是{sex}
    回答时，如果性别是女，用她。性别是男，用他。
    注意返回在100-150字
    用json的格式返回. 格式为 {{”response“:姻缘分析情况}}
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
        messages=[{"role": "system", "content": prompt},
                {"role": "user", "content":f"八字为:{bazi}\n\nn五行为:{wuxing}\n\n十神为：{shishen}"}],
        max_tokens = 2048,
        temperature = 0,
        response_format={"type": "json_object"}

    )
    string_res = completion.choices[0].message.content.strip()
    string_res = json.loads(string_res)

    return string_res["response"]
def mingyunGPT(bazi,mingyun,sex):
    if sex=='女':
        mingyun=mingyun.replace('妻','夫')
    prompt = f"""
    你是个算命大师，我现在会把某个人的八字和命理告诉你
    注意此人的性别是{sex}
    回答时，如果性别是女，用她。性别是男，用他。
    请根据我发的八字和命理给出到对应的命运描述，并帮我组织下语言发我白话文，注意不要出现'根据你提供xxx'
    注意返回在100-150字
    用json的格式返回. 格式为 {{”response“:命运描述的白话文}}
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
        messages=[{"role": "system", "content": prompt},
                {"role": "user", "content":f"八字为：{bazi} \n\n 命运为：{mingyun}"}],
        max_tokens = 2048,
        temperature = 0,
        response_format={"type": "json_object"}

    )
    string_res = completion.choices[0].message.content.strip()
    string_res = json.loads(string_res)

    return string_res["response"]

def chushenGPT(bazi,chushen,sex):
    prompt = f"""
    你是个算命大师，我现在会把某个人的八字告诉你
    请根据我发的八字和出身情况扩写成个人的出身情况
    注意此人的性别是{sex}
    回答时，如果性别是女，用她。性别是男，用他。
    注意返回在100-150字
    注意前后逻辑一致性
    用json的格式返回. 格式为 {{”response“:出身情况}}
    """

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
        messages=[{"role": "system", "content": prompt},
                {"role": "user", "content":f"八字为：{bazi} \n\n出身情况: {chushen}"}],
        max_tokens = 2048,
        temperature = 0,
        response_format={"type": "json_object"}

    )
    string_res = completion.choices[0].message.content.strip()
    string_res = json.loads(string_res)

    return string_res["response"]

import io
import os

import sys
import threading

def capture_print(func):
    def wrapper(*args, **kwargs):
        lock = threading.Lock()
        captured_output = io.StringIO()
        current_stdout = sys.stdout
        try:
            sys.stdout = captured_output
            # 获取锁
            lock.acquire()
            res = func(*args, **kwargs)
            return res,captured_output.getvalue()
        finally:
            # 释放锁
            lock.release()
            sys.stdout = current_stdout
    return wrapper


@capture_print
def bazipaipan(year, month, day, time, gender,name=None,tg_bot=False):
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
    if tg_bot:
        start="🔹"
        end = ""
    else:     
        start = "<b>"
        end = "</b>"
    if name:
        print(f"{start}姓名：{end}{name}")
    sex = '女' if gender else '男' # 1 为男，0 为女
    print(f"{start}性别：{end}{sex}")
    day_lunar = sxtwl.fromSolar(int(year), int(month), int(day))


    lunar_birthday = day_lunar.getLunarYear() # 农历
    Lleap = "闰" if day_lunar.isLunarLeap() else ""
    lunar = Lunar.fromYmdHms(day_lunar.getLunarYear(), day_lunar.getLunarMonth(), day_lunar.getLunarDay(),int(time), 0, 0)
    zodiac = lunar.getYearShengXiao()
    eightWord = lunar.getEightChar() # 八字
    print(f"{start}生肖：{end}{zodiac}")
    print(f"{start}公历：{end}", end='')
    print("{}年{}月{}日{}时".format(day_lunar.getSolarYear(), day_lunar.getSolarMonth(), day_lunar.getSolarDay(),eightWord.getTime()[1]))
    print(f"{start}农历：{end}", end='')
    print("{}年{}{}月{}日{}时".format(day_lunar.getLunarYear(), Lleap, day_lunar.getLunarMonth(), day_lunar.getLunarDay(),eightWord.getTime()[1]))

    print(f"{start}八字：{end}{eightWord}")
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

    wuXing = lunar.getBaZiWuXing()  # 五行
    print(f"{start}五行：{end}", end='')
    print(' '.join(wuXing))
    print(f"{start}命主：{end}{mingzhu}{wuXing[2][0]}")
    scores = {"金":0, "木":0, "水":0, "火":0, "土":0} # 五行分数
    for item in gans:  
        scores[gan5[item]] += 5

    for item in list(zhis) + [zhis.month]:  
        for gan in zhi5[item]:
            scores[gan5[gan]] += zhi5[item][gan]

    
    elements_with_scores = [f"{element}{score}" for element, score in scores.items()]
    result = "，".join(elements_with_scores)
    print(f"{start}五行得分：{end}{result}")
    print(f"{start}五行是否有缺：{end}", end='')
    all_elements = {'金', '木', '水', '火', '土'}
    elements = set(''.join(wuXing))
    missing = all_elements - elements
    if len(missing)==0:
        print("您八字中五行诸全，五行不缺。")
    else:
        print("您八字中五行相对缺"+"，".join(missing)+"。")
    print(f"{start}命理分析：{end}")
    zhus = [item for item in zip(gans, zhis)]
    sum_index = ''.join([mingzhu, '日', *zhus[3]])
    if sum_index in summarys:     
        mingyun_analysis = mingyunGPT(eightWord,summary[sum_index],sex)
    else:
        mingyun_analysis = mingyunGPT(eightWord,f"此人生于{sum_index}",sex)

    print(mingyun_analysis)

    scores_table = {
    "正财": (2.5, 2),
    "正官": (2.5, 2),
    "正印": (2, 1.5),
    "比肩": (0.5, 0.5),
    "食神": (1, 0.5),
    "偏财": (1.5, 1),
    "七杀": (-2, -1.5),
    "偏印": (-0.5, 0),
    "劫财": (-2, -1.5),
    "伤官": (-1, -0.5),
    }
    score = 0
    for ts in tianganshishen[:2]:
        score+=scores_table[ts][0]
    for ds in dizhishishen[:2]:
        score+=scores_table[ds][1]
    if score>=7:
        birth = '极好'
    elif score>=3:
        birth = '较好'
    elif score>=-2:
        birth = '尚可'
    elif score>=-5:
        birth = '一般'
    else:
        birth = '寒门'
    chushen_analysis = chushenGPT(eightWord,birth,sex)
    print(chushen_analysis)
    print(f"{start}生肖分析：{end}\n{sx_xingge[zodiac]}")
    print(f"{start}财运分析：{end}")
    caiyun_analysis = caiyunGPT(eightWord,shishen,scores,sex)
    print(caiyun_analysis)
    print(f"{start}姻缘分析：{end}")
    yinyuan_analysis = yinyuanGPT(eightWord,shishen,scores,sex)
    print(yinyuan_analysis)
    print(f"{start}性格分析：{end}")
    xingge_analysis = xinggeGPT(eightWord,shishen,scores,sex)
    print(xingge_analysis)
    print("---------------")
    print("十神:", end='')
    print('\t'.join(shishen))
    print("十神神煞：")
    for ss in shishen:
        print(f"\t{ss}:{shishen_shensha[ss]}")
    print("十神分析：")
    print(shishenGPT(shishen,sex))
    sum_index = ''.join([mingzhu, '日', *zhus[3]])
    print(sum_index)
    if summary.get(sum_index):
        print(summary[sum_index])

    print("大运流年分析：")
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
        if day_.hasJieQi() and day_.getJieQi() % 2 == 1:
                break
            #break        
        birthday += datetime.timedelta(days=direction)
        count += 1
    ages = [(round(count/3 + 10*i), round(int(year) + 10*i + count//3)) for i in range(8)]
    ages.insert(0,(0,int(year)))
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
                
        out = "大运:{1:<4d}{2:<5s}{3} {15} {14} {13}  {4}:{5}{8}{6:{0}<6s}{12}{7}{8}{9} {10:{0}<15s} {11}".format(
            chr(12288), int(value[0]), '', dayuns[seq],ten_deities[mingzhu][gan_], gan_,check_gan(gan_, gans), 
            zhi_, yinyang(zhi_), '', zhi5_, zhi__,empty, fu, '', '') 
        gan_index = Gan.index(gan_)
        zhi_index = Zhi.index(zhi_)
        out = out + jia + get_shens(gans, zhis, gan_, zhi_)
        print(out)
        current_year = datetime.datetime.now().year
        zhis2 = list(zhis) + [zhi_]
        gans2 = list(gans) + [gan_]
        if value[0] > 100:
            continue
        for i in range(10):
            _year = value[1] + i
            if value[1]<current_year:
                continue
            if _year-current_year>20:
                continue

            day2 = sxtwl.fromSolar(value[1] + i, 5, 1)    
            yTG = day2.getYearGZ()
            gan2_ = Gan[yTG.tg]
            zhi2_ = Zhi[yTG.dz]
            fu2 = '*' if (gan2_, zhi2_) in zhus else " "
            #print(fu2, (gan2_, zhi2_),zhus)
            
            zhi6_ = ''
            for gan in zhi5[zhi2_]:
                zhi6_ = zhi6_ + "{}{}{}　".format(gan, gan5[gan], ten_deities[mingzhu][gan])        
            
            # 大运地支关系
            zhi__ = set() # 大运地支关系
            for item in zhis2:
            
                for type_ in zhi_atts[zhi2_]:
                    if type_ == '破':
                        continue
                    if item in zhi_atts[zhi2_][type_]:
                        zhi__.add(type_ + ":" + item)
            zhi__ = '  '.join(zhi__)
            
            empty = chr(12288)
            if zhi2_ in empties[zhus[2]]:
                empty = '空'       
            out = "{1:>3d}岁 {2:<5d}流年:{3} {15} {14} {13}  {4}:{5}{8}{6:{0}<6s}{12}{7}{8}{9} - {10:{0}<13s} {11}".format(
                chr(12288), int(value[0]) + i, value[1] + i, gan2_+zhi2_,ten_deities[mingzhu][gan2_], gan2_,check_gan(gan2_, gans2), 
                zhi2_, yinyang(zhi2_), ten_deities[mingzhu][zhi2_], zhi6_, zhi__,empty, fu2, nayins[(gan2_, zhi2_)], ten_deities[mingzhu][zhi2_]) 
            jia = ""
            if gan2_ in gans2:
                for i in range(5):
                    if gan2_ == gans2[i]:
                        zhi1 = zhis2[i]
                        if abs(Zhi.index(zhi2_) - Zhi.index(zhis2[i])) == 2:
                            # print(2, zhi2_, zhis2[i])
                            jia = jia + "  --夹：" +  Zhi[( Zhi.index(zhi2_) + Zhi.index(zhis2[i]) )//2]
                        if abs( Zhi.index(zhi2_) - Zhi.index(zhis2[i]) ) == 10:
                            # print(10, zhi2_, zhis2[i])
                            jia = jia + "  --夹：" +  Zhi[(Zhi.index(zhi2_) + Zhi.index(zhis2[i]))%12]  

                        if (zhi1 + zhi2_ in gong_he) and (gong_he[zhi1 + zhi2_] not in zhis):
                            jia = jia + "  --拱：" + gong_he[zhi1 + zhi2_]
                            
            out = out + jia + get_shens(gans, zhis, gan2_, zhi2_)
            all_zhis = set(zhis2) | set(zhi2_)
            if set('戌亥辰巳').issubset(all_zhis):
                out = out + "  天罗地网：戌亥辰巳"
            if set('寅申巳亥').issubset(all_zhis) and len(set('寅申巳亥')&set(zhis)) == 2 :
                out = out + "  四生：寅申巳亥"   
            if set('子午卯酉').issubset(all_zhis) and len(set('子午卯酉')&set(zhis)) == 2 :
                out = out + "  四败：子午卯酉"  
            if set('辰戌丑未').issubset(all_zhis) and len(set('辰戌丑未')&set(zhis)) == 2 :
                out = out + "  四库：辰戌丑未"             
            print(out)


    return mingyun_analysis,chushen_analysis
if __name__ =="__main__":
    year = '2024'
    month = '7'
    day = '25'
    time = '10'

    print(bazipaipan(year,month,day,time,True))
