import json
import sxtwl
import os
from lunar_python import Lunar
import collections
from collections import OrderedDict
from openai import OpenAI

client = OpenAI()
Gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
Zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
gan5 = {"甲":"木", "乙":"木", "丙":"火", "丁":"火", "戊":"土", "己":"土", 
        "庚":"金", "辛":"金", "壬":"水", "癸":"水"}
zhi1 = {"子":"水", "丑":"土", "寅":"木", "卯":"木", "辰":"土", "巳":"火",
        "午":"火", "未":"土", "申":"金", "酉":"金", "戌":"土", "亥":"水"}
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
situations_text = {
    "单边涨":"该币种近期用神得力，有望上涨，建议逢低买入，已有持仓，建议继续持有。",
    "单边跌":"该币种近期忌神得力，有下跌风险，建议持币观望，如已有持仓，建议分批逢高卖出，注意风险。",
    "横盘":"该币种近期并无喜忌，行情相对平淡。",
    "剧烈震荡":"该币种近期喜忌参半，有可能走出剧烈震荡行情，如有杠杆建议减小杠杆，机会很多，但需注意风险。"
}


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
            return captured_output.getvalue()
        finally:
            # 释放锁
            lock.release()
            sys.stdout = current_stdout
    return wrapper


@capture_print
def get_asset_rules(name, year, month, day, time, pc=None):
    if pc:
        start = "<b>"
        end = "</b>"
    else:
        start="🔹"
        end = ""     

    def wuxing_liuyue(name, year, month, day, time, pc=None):

        solar_birthday = sxtwl.fromSolar(int(year), int(month),int(day))  # 公历生日
        Lleap = "闰" if solar_birthday.isLunarLeap() else ""
        # 农历生日
        lunar_birthday = Lunar.fromYmdHms(solar_birthday.getLunarYear(), solar_birthday.getLunarMonth(), solar_birthday.getLunarDay(), int(time), 0, 0)

        zodiac = lunar_birthday.getYearShengXiao() # 生肖
        eightWord = lunar_birthday.getEightChar() # 八字
        print(f"{start}Name: {end}{name}")
        print(f"{start}公历：{end}", end='')
        print("{}年{}月{}日{}时".format(solar_birthday.getSolarYear(), solar_birthday.getSolarMonth(), solar_birthday.getSolarDay(),eightWord.getTime()[1]))
        print(f"{start}农历：{end}", end='')
        print("{}年{}{}月{}日{}时".format(solar_birthday.getLunarYear(), Lleap, solar_birthday.getLunarMonth(), solar_birthday.getLunarDay(),eightWord.getTime()[1]))

        print(f"{start}八字：{end}{eightWord}")
        gz = solar_birthday.getHourGZ(int(time))
        yTG = solar_birthday.getYearGZ()
        mTG = solar_birthday.getMonthGZ()
        dTG  = solar_birthday.getDayGZ()
        Gans = collections.namedtuple("Gans", "year month day time")
        Zhis = collections.namedtuple("Zhis", "year month day time")
        gans = Gans(year=Gan[yTG.tg], month=Gan[mTG.tg], 
                    day=Gan[dTG.tg], time=Gan[gz.tg])
        zhis = Zhis(year=Zhi[yTG.dz], month=Zhi[mTG.dz], 
                    day=Zhi[dTG.dz], time=Zhi[gz.dz])
        mingzhu = gans.day

        tianganshishen = lunar_birthday.getBaZiShiShenGan()
        dizhishishen = lunar_birthday.getBaZiShiShenZhi()
        nianshishen = lunar_birthday.getBaZiShiShenYearZhi()
        yueshishen = lunar_birthday.getBaZiShiShenMonthZhi()
        rishishen = lunar_birthday.getBaZiShiShenDayZhi()
        shishishen = lunar_birthday.getBaZiShiShenTimeZhi()
        shishen = [tianganshishen[0], tianganshishen[1], tianganshishen[3]]
        shishen.extend(nianshishen)
        shishen.extend(yueshishen)
        shishen.extend(rishishen)
        shishen.extend(shishishen)

        wuXing = lunar_birthday.getBaZiWuXing()  # 五行
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
        wuxing_scores = "，".join(elements_with_scores)
        print(f"{start}五行得分：{end}{wuxing_scores}")
        print(f"{start}五行是否有缺：{end}", end='')
        all_elements = {'金', '木', '水', '火', '土'}
        elements = set(''.join(wuXing))
        missing = all_elements - elements
        if len(missing)==0:
            print("八字中五行诸全，五行不缺。")
        else:
            print("八字中五行相对缺"+"，".join(missing)+"。")

        yun = eightWord.getYun(1) # 运
        daYunArr = yun.getDaYun() # 大运
        liuNianArr = daYunArr[0].getLiuNian() # 流年
        liuYueArr = liuNianArr[0].getLiuYue() # 流月
        # 将流月与五行进行对应
        liuyue_wuxing = []
        for liuYue in liuYueArr:
            ganzhi = liuYue.getGanZhi()
            wuxing = gan5[ganzhi[0]] + zhi1[ganzhi[1]]
            liuyue_wuxing.append(wuxing)

        return scores, liuyue_wuxing


    def guanxi(scores, liuyue_wuxing):
        # 对五行得分进行大小排序
        # 计算规则：根据五行得分对五行进行大小排列后，流月五行与它的关系，得出以下4种情况
        # 1. 单边涨：流月至少一个五行与得分最大五行相同
        # 2. 单边跌：流月至少一个五行与得分最小五行相同
        # 3. 横盘：流月五行与得分最大最小五行都无关
        # 4. 剧烈震荡：流月五行一个与最大相同，一个与最小相同
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        texts = []

        for wuxing in liuyue_wuxing:
            if wuxing[0] == sorted_scores[0][0] and wuxing[1] == sorted_scores[4][0]:
                texts.append(situations_text["剧烈震荡"])
            elif wuxing[0] == sorted_scores[0][0]:
                texts.append(situations_text["单边涨"])
            elif wuxing[0] == sorted_scores[4][0]:
                texts.append(situations_text["单边跌"])
            elif wuxing[1] == sorted_scores[0][0]:
                texts.append(situations_text["单边涨"])
            elif wuxing[1] == sorted_scores[4][0]:
                texts.append(situations_text["单边跌"])
            else:
                texts.append(situations_text["横盘"])
        return texts
        

    def month_forecast(liuyue_wuxing, texts):
        prompt = f"""
        你是一个算命大师主要负责内容扩写，
        我现在提供给你对应的文案```{texts}```，
        请根据文案进行自由发挥扩写补充，
        要求返回文案在100-150字左右，
        文案不可以重复，做到前后逻辑通顺。
        
        请用json格式返回，格式为{{"response":文案扩写}}
        """

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"流月五行为：{liuyue_wuxing} \n\n 文案：{texts}"} 
            ],
            # max_tokens=2048,
            temperature=1,
            response_format={"type": "json_object"}
        )
        try:
            string_res = completion.choices[0].message.content.strip()
            string_res = json.loads(string_res)
            return string_res["response"]

        except:
            string_res = completion.choices[0].message.content.strip()
            print(string_res)
    scores, liuyue_wuxing = wuxing_liuyue(name, year, month, day, time, pc=pc)
    texts = guanxi(scores, liuyue_wuxing)
    import datetime
    current_month = datetime.datetime.now().month
    forcast = month_forecast(liuyue_wuxing[current_month-1], texts[current_month-1])    
    print(f"{start}月运势预测：{end}")
    print(f"流月五行为{liuyue_wuxing[current_month-1]}。"+forcast)