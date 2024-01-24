import io
import os
import sys
from lunar_python import Lunar, Solar

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
def baziMatch(year,month,day,t_ime,year_a,month_a,day_a,t_ime_a,name=None,coin_data=None,own=None):
    def safe_convert(x):
        r = 100 - x
        s = r % 9
        return 2 if s == 5 else s

    def safe_convert_a(x):
        r = x - 4
        s = r % 9
        return 8 if s == 5 else s

    def shengchen(i):
        i = str(i).zfill(2)  # 确保输入是两位字符串
        mapping = {
            "00": "庚辰", "01": "辛丑", "02": "壬寅", "03": "癸卯",
            "04": "甲辰", "05": "乙已", "06": "丙午", "07": "丁未",
            "08": "戊申", "09": "己酉", "10": "庚戌", "11": "辛亥",
            "12": "壬子", "13": "癸丑", "14": "甲寅", "15": "乙卯",
            "16": "丙辰", "17": "丁巳", "18": "戊午", "19": "己未",
            "20": "庚申", "21": "辛酉", "22": "壬戌", "23": "癸亥",
            "24": "甲子", "25": "乙丑", "26": "丙寅", "27": "丁卯",
            "28": "戊辰", "29": "己巳", "30": "庚午", "31": "辛未",
            "32": "壬申", "33": "癸酉", "34": "甲戌", "35": "乙亥",
            "36": "丙子", "37": "丁丑", "38": "戊寅", "39": "己卯",
            "40": "庚辰", "41": "辛巳", "42": "壬午", "43": "癸未",
            "44": "甲申", "45": "乙酉", "46": "丙戌", "47": "丁亥",
            "48": "戊子", "49": "己丑", "50": "庚寅", "51": "辛卯",
            "52": "壬辰", "53": "癸巳", "54": "甲午", "55": "乙未",
            "56": "丙申", "57": "丁酉", "58": "戊戌", "59": "己亥",
            "60": "庚子", "61": "辛丑", "62": "壬寅", "63": "癸卯",
            "64": "甲辰", "65": "乙巳", "66": "丙午", "67": "丁未",
            "68": "戊申", "69": "己酉", "70": "庚戌", "71": "辛亥",
            "72": "壬子", "73": "癸丑", "74": "甲寅", "75": "乙卯",
            "76": "丙辰", "77": "丁巳", "78": "戊午", "79": "己未",
            "80": "庚申", "81": "辛酉", "82": "壬戌", "83": "癸亥",
            "84": "甲子", "85": "乙丑", "86": "丙寅", "87": "丁卯",
            "88": "戊辰", "89": "己巳", "90": "庚午", "91": "辛未",
            "92": "壬申", "93": "癸酉", "94": "甲戌", "95": "乙亥",
            "96": "丙子", "97": "丁丑", "98": "戊寅", "99": "己卯"
        }
        return mapping.get(i, "不存在")

    def mgong(i):
        mapping = ["离", "坎", "坤", "震", "巽", "坤", "乾", "兑", "艮", "离"]
        return mapping[i]

    def mgong_a(i):
        mapping = ["离", "坎", "坤", "震", "巽", "艮", "乾", "兑", "艮", "离"]
        return mapping[i]

    def safew(s):
        return s.replace("|", "│").replace("<", "&lt;").replace(">", "&gt;").replace("\r", "").replace("\t", "").replace("\n", "<br><br>&nbsp;&nbsp;&nbsp;&nbsp;").replace(" ", "&nbsp;")

    def dxsz(i):
        mapping = ["东", "东", "西", "东", "东", "西", "西", "西", "西", "东"]
        return mapping[i]

    def dxsz_a(i):
        mapping = ["东", "东", "西", "东", "东", "西", "西", "西", "西", "东"]
        return mapping[i]

    def fangwei(i):
        mapping = ["坐南向北", "坐北向南", "坐西南向东北", "坐东向西", "坐东南向西北", "坐西南向东北", "坐西北向东南", "坐西向东", "坐东北向西南", "坐南向北"]
        return mapping[i]

    def fangwei_a(i):
        mapping = ["坐南向北", "坐北向南", "坐西南向东北", "坐东向西", "坐东南向西北", "坐东北向西南", "坐西北向东南", "坐西向东", "坐东北向西南", "坐南向北"]
        return mapping[i]

    def pdyl(x, y):
        if x == 31:
            return 1 if y in [32, 33, 34, 35, 36, 37, 38, 41] else 0
        elif x == 32:
            return 1 if y in [33, 34, 38, 39, 40, 41, 30] else 0
        elif x == 33:
            return 1 if y in [32, 35, 36, 37, 38, 39, 40, 41] else 0
        elif x == 34:
            return 1 if y in [32, 35, 36, 37, 38, 39, 40, 41] else 0
        elif x == 35:
            return 1 if y in [31, 33, 34, 39, 40, 41, 30] else 0
        elif x == 36:
            return 1 if y in [31, 32, 35, 38, 39, 40, 41, 30] else 0
        elif x == 37:
            return 1 if y in [31, 32, 35, 38, 39, 40, 41, 30] else 0
        elif x == 38:
            return 1 if y in [31, 32, 33, 34, 39, 40, 41, 30] else 0
        elif x == 39:
            return 1 if y in [31, 33, 34, 35, 36, 37, 38, 30] else 0
        elif x == 40:
            return 1 if y in [31, 33, 34, 36, 37, 38, 39, 30] else 0
        elif x == 41:
            return 1 if y in [31, 32, 33, 34, 35, 39, 40] else 0
        elif x == 30:
            return 1 if y in [32, 33, 34, 35, 36, 37, 38, 41] else 0
        return None  # Default case if none of the conditions match

    # Translation of PHP arrays to Python dictionaries
    b = {31: "鼠", 32: "牛", 33: "虎", 34: "兔", 35: "龙", 36: "蛇", 37: "马", 38: "羊", 39: "猴", 40: "鸡", 41: "狗", 30: "猪"}
    c = {31: "水", 32: "水", 33: "木", 34: "木", 35: "木", 36: "火", 37: "火", 38: "火", 39: "金", 40: "金", 41: "金", 30: "水"}

    # 天干
    d = {21: "a", 22: "a", 23: "b", 24: "b", 25: "c", 26: "c", 27: "d", 28: "d", 29: "e", 20: "e"}
    da = {21: "1", 22: "0", 23: "1", 24: "0", 25: "1", 26: "0", 27: "1", 28: "0", 29: "1", 20: "0"}

    # 天干合化
    e = {21: "土", 22: "金", 23: "水", 24: "木", 25: "火", 26: "土", 27: "金", 28: "水", 29: "木", 20: "火"}

    a = {21: "甲", 22: "乙", 23: "丙", 24: "丁", 25: "戊", 26: "己", 27: "庚", 28: "辛", 29: "壬", 20: "癸",
        31: "子", 32: "丑", 33: "寅", 34: "卯", 35: "辰", 36: "巳", 37: "午", 38: "未", 39: "申", 40: "酉", 41: "戌", 30: "亥",
        1: "比肩", 2: "劫财", 3: "食神", 4: "伤官", 5: "偏财", 6: "正财", 7: "七杀", 8: "正官", 9: "偏印", 0: "正印"}

    yearday = 0
    # 确定节气 yz 月支  起运基数 qyjs
    md = month * 100 + day

    if md >= 1208 or md <= 105:
        mz = 1
        qyjs = ((month - 1 if md > 1200 else 0) * 30 + day - 4) / 3
    elif md <= 203:
        mz = 2
        qyjs = ((month - 1) * 30 + day - 6) / 3
    else:
        mz = (md - 204) // 100 + 3
        qyjs = ((month - (mz - 1)) * 30 + day - (mz + 1)) / 3
        if mz >= 11:
            mz -= 12

    # 确定年干和年支 yg 年干 yz 年支
    if md >= 204 and md <= 1231:
        yg = (year - 3) % 10
        yz = (year - 3) % 12
    elif md >= 101 and md <= 203:
        yg = (year - 4) % 10
        yz = (year - 4) % 12

    if mz > 2 and mz <= 11:
        mg = (yg * 2 + mz + 8) % 10
    else:
        mg = (yg * 2 + mz) % 10

    yearlast = (year - 1) * 5 + (year - 1) // 4 - (year - 1) // 100 + (year - 1) // 400
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    for i in range(1, month):
        if i == 2:
            if year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
                yearday += 29
            else:
                yearday += 28
        else:
            yearday += days_in_month[i - 1]

    yearday += day

    # 计算日的六十甲子数 day60
    day60 = (yearlast + yearday + 6015) % 60

    # 确定日干 dg 日支 dz
    dg = day60 % 10
    dz = day60 % 12

    # 确定时干 tg 时支 tz
    tz = (t_ime + 3) // 2 % 12

    if tz == 0:
        tg = (dg * 2 + tz) % 10
    else:
        tg = (dg * 2 + tz + 8) % 10

    # 确定各地支所纳天干
    def get_nagan(zhi):
        mapping = {1: 0, 2: 6, 8: 6, 3: 1, 4: 2, 5: 5, 11: 5, 6: 3, 7: 4, 9: 7, 10: 8, 0: 9}
        return mapping.get(zhi, 0)

    yzg = get_nagan(yz)
    mzg = get_nagan(mz)
    dzg = get_nagan(dz)
    tzg = get_nagan(tz)

    # 确定各支对应的十神
    def get_shishen(gan1, gan2):
        return ((gan1 + 11 - gan2) + ((gan2 + 1) % 2) * ((gan1 + 10 - gan2) % 2) * 2) % 10

    ygs = get_shishen(yg, dg)
    mgs = get_shishen(mg, dg)
    tgs = get_shishen(tg, dg)
    yzs = get_shishen(yzg, dg)
    mzs = get_shishen(mzg, dg)
    dzs = get_shishen(dzg, dg)
    tzs = get_shishen(tzg, dg)

    # 确定节气、月支和起运基数
    md_a = month_a * 100 + day_a
    if 204 <= md_a <= 305:
        mz_a = 3
    elif 306 <= md_a <= 404:
        mz_a = 4
    elif 405 <= md_a <= 504:
        mz_a = 5
    elif 505 <= md_a <= 605:
        mz_a = 6
    elif 606 <= md_a <= 706:
        mz_a = 7
    elif 707 <= md_a <= 807:
        mz_a = 8
    elif 808 <= md_a <= 907:
        mz_a = 9
    elif 908 <= md_a <= 1007:
        mz_a = 10
    elif 1008 <= md_a <= 1106:
        mz_a = 11
    elif 1107 <= md_a <= 1207:
        mz_a = 0
    elif 1208 <= md_a <= 1231 or 101 <= md_a <= 105:
        mz_a = 1
    elif 106 <= md_a <= 203:
        mz_a = 2

    qyjs_a = ((month_a - (2 if mz_a != 1 else 1)) * 30 + day_a - (4 if mz_a != 1 else 4)) / 3

    # 确定年干和年支
    if 204 <= md_a <= 1231:
        yg_a = (year_a - 3) % 10
        yz_a = (year_a - 3) % 12
    else:
        yg_a = (year_a - 4) % 10
        yz_a = (year_a - 4) % 12

    # 确定月干
    mg_a = (yg_a * 2 + mz_a + (8 if mz_a > 2 and mz_a <= 11 else 0)) % 10

    # 从公元0年到目前年份的天数
    yearlast_a = (year_a - 1) * 5 + (year_a - 1) // 4 - (year_a - 1) // 100 + (year_a - 1) // 400

    # 计算年的天数
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    yearday_a = sum(month_days[:month_a - 1]) + day_a
    if month_a > 2 and (year_a % 4 == 0 and year_a % 100 != 0 or year_a % 400 == 0):
        yearday_a += 1

    # 计算日的六十甲子数
    day60_a = (yearlast_a + yearday_a + 6015) % 60

    # 确定日干和日支
    dg_a = day60_a % 10
    dz_a = day60_a % 12

    # 确定时干和时支
    tz_a = (t_ime_a + 3) // 2 % 12
    tg_a = (dg_a * 2 + tz_a + (8 if tz_a != 0 else 0)) % 10

    # 确定各地支所纳天干
    def get_nagan(zhi):
        mapping = {1: 0, 2: 6, 8: 6, 3: 1, 4: 2, 5: 5, 11: 5, 6: 3, 7: 4, 9: 7, 10: 8, 0: 9}
        return mapping.get(zhi, 0)

    yzg_a = get_nagan(yz_a)
    mzg_a = get_nagan(mz_a)
    dzg_a = get_nagan(dz_a)
    tzg_a = get_nagan(tz_a)

    # 确定各支对应的十神
    def get_shishen(gan1, gan2):
        return ((gan1 + 11 - gan2) + ((gan2 + 1) % 2) * ((gan1 + 10 - gan2) % 2) * 2) % 10

    ygs_a = get_shishen(yg_a, dg_a)
    mgs_a = get_shishen(mg_a, dg_a)
    tgs_a = get_shishen(tg_a, dg_a)
    yzs_a = get_shishen(yzg_a, dg_a)
    mzs_a = get_shishen(mzg_a, dg_a)
    dzs_a = get_shishen(dzg_a, dg_a)
    tzs_a = get_shishen(tzg_a, dg_a)

    # 女命已算完，完成年月日时各干支十神的确定
    # 求出年份后两位数
    f_n = str(year)[-2:]
    f_v = str(year_a)[-2:]

    # 求出所属宫位（数值表示）
    z_n = safe_convert(int(f_n))
    z_v = safe_convert_a(int(f_v))
    # 对特定的宫位进行特殊处理
    z_nn = "2" if z_n == 5 else z_n
    z_vv = "8" if z_v == 5 else z_v

    z_nn = "9" if z_n == 0 else z_n
    z_vv = "9" if z_v == 0 else z_v

    # 推出年干年支
    qq_n = shengchen(f_n)
    qq_v = shengchen(f_v)

    # 求出所属宫位（汉字表示）
    m_n = mgong(z_n)
    m_v = mgong(z_v)

    # 宫位合婚计算
    bb_values = {
        (1, 4): 30, (4, 1): 30, (2, 8): 30, (8, 2): 30,
        (3, 9): 30, (9, 3): 30, (6, 7): 30, (7, 6): 30,
        (1, 8): 0,  (8, 1): 0,  (2, 4): 0,  (4, 2): 0,
        (3, 6): 0,  (6, 3): 0,  (9, 7): 0,  (7, 9): 0,
        (1, 9): 30, (9, 1): 30, (2, 6): 30, (6, 2): 30,
        (3, 4): 30, (4, 3): 30, (8, 7): 30, (7, 8): 30,
        (1, 6): 0,  (6, 1): 0,  (2, 9): 0,  (9, 2): 0,
        (3, 8): 0,  (8, 3): 0,  (4, 7): 0,  (7, 4): 0,
        (1, 7): 0,  (7, 1): 0,  (2, 3): 0,  (3, 2): 0,
        (4, 6): 0,  (6, 4): 0,  (8, 9): 0,  (9, 8): 0,
        (1, 3): 30, (3, 1): 30, (2, 7): 30, (7, 2): 30,
        (4, 9): 30, (9, 4): 30, (8, 6): 30, (6, 8): 30,
        (1, 2): 0,  (2, 1): 0,  (7, 3): 0,  (3, 7): 0,
        (4, 8): 0,  (8, 4): 0,  (9, 6): 0,  (6, 9): 0,
        (1, 1): 15, (2, 2): 15, (3, 3): 15, (4, 4): 15,
        (6, 6): 15, (7, 7): 15, (8, 8): 15, (9, 9): 15
    }
    bb = bb_values.get((z_nn, z_vv), 0)  # 使用默认值0


    # 年支合
    c = 20 if c[30 + yz_a] == c[30 + yz] else 0

    # 月令合
    yh = 5 if a[30 + mz_a] == a[30 + mz] else 0

    # 日合
    rh = 5 if a[20 + dg_a] != a[20 + dg] and e[20 + dg_a] == e[20 + dg] else 0
    rrh = 25 if d[20 + dg_a] == d[20 + dg] else 0

    # 子女同步
    erzi = "男" if tgs in [7, 8] else "女"
    erzi_a = "男" if tgs_a in [5, 6] else "女"
    # (其他天干十神对应的子女判断)
    ez = 15 if erzi_a == erzi else 0

    # 总得分
    total_score = bb + c + yh + rh + rrh + ez


    lunar = Solar.fromYmd(year, month, day).getLunar()
    baZi = lunar.getEightChar()
    yun = baZi.getYun(0)
    daYunArr = yun.getDaYun()

    yearList = []
    ageList = []

    for i in range(0, len(daYunArr)):
        daYun = daYunArr[i]
        yearList.append(str(daYun.getStartYear()))
        ageList.append(str(daYun.getStartAge()) + "岁")
    print("-"*120)
    if name is None or own==True:
        print(f"本人信息：")
        print(f"出生地时间（公历）：{year}年 {month}月 {day}日 {t_ime}时")
        print("胎元：")
        # print(f"十神：  {ygs}   {mgs}   日主   {tgs}")
        print(f"乾造    {a[20+yg]+a[30+yz]}   {a[20+mg]+a[30+mz]}   {a[20+dg]+a[30+dz]}   {a[20+tg]+a[30+tz]}")
        print(f"支十神：{a[yzs]}   {a[mzs]}   {a[dzs]}   {a[tzs]}")
        print("十神")
        for i in range(1, 9):
            sx = ((mg + 10) - i) % 10
            xy = ((sx + 11 - dg) + ((dg + 1) % 2) * ((sx + 10 - dg) % 2) * 2) % 10
            print(a[xy],end="   ")
        print()
        print("大运")
        for i in range(1, 9):
            print(f"{a[20 + ((mg + 10 - i) % 10)]}{a[30 + ((mz + 12 - i) % 12)]}", end="   ")
        print()

        # Print the ages
        print("     ".join(ageList))
        # Print the years
        print("   ".join(yearList))
        print ('')
        print ('出生' + str(yun.getStartYear()) + '年' + str(yun.getStartMonth()) + '个月' + str(yun.getStartDay()) + '天后起运')
        print ('阳历' + yun.getStartSolar().toYmd() + '后起运')
        print(f"生肖为：{b[30+yz]}")
        print(f"命宫为：{m_n}")
        print("-"*120)
    if name is not None:
        print(f"资产信息：")
        print(f"资产名字：{name}")
        print(f"创世块时间（公历）：{year_a}年 {month_a}月 {day_a}日 {t_ime_a}时")

    # else:
    #     # print(f"他人信息：")
    #     # print(f"出生地时间（公历）：{year_a}年 {month_a}月 {day_a}日 {t_ime_a}时")
    # # print(f"十神：  {ygs_a}   {mgs_a}   日主   {tgs_a}")
        # print("胎元：")
        print(f"乾造    {a[20+yg_a]+a[30+yz_a]}   {a[20+mg_a]+a[30+mz_a]}   {a[20+dg_a]+a[30+dz_a]}   {a[20+tg_a]+a[30+tz_a]}")
        print(f"支十神：{a[yzs_a]}   {a[mzs_a]}   {a[dzs_a]}   {a[tzs_a]}")
        print("十神")
        for i in range(1, 9):
            sx_a = ((mg_a + 10) - i) % 10
            xy_a = ((sx_a + 11 - dg_a) + ((dg_a + 1) % 2) * ((sx_a + 10 - dg_a) % 2) * 2) % 10
            print(a[xy_a],end="   ")
        print()
        print("大运")
        for i in range(1, 9):
            print(f"{a[20 + ((mg_a + 10 - i) % 10)]}{a[30 + ((mz_a + 12 - i) % 12)]}", end="   ")
        print()
        lunar = Solar.fromYmd(year_a, month_a, day_a).getLunar()
        baZi = lunar.getEightChar()
        yun = baZi.getYun(0)
        daYunArr = yun.getDaYun()
        yearList = []
        ageList = []

        for i in range(0, len(daYunArr)):
            daYun = daYunArr[i]
            yearList.append(str(daYun.getStartYear()))
            ageList.append(str(daYun.getStartAge()))

        # print("     ".join(ageList))
    # Print the years
        print("   ".join(yearList))
        print ('')
        # print ('出生' + str(yun.getStartYear()) + '年' + str(yun.getStartMonth()) + '个月' + str(yun.getStartDay()) + '天后起运')
        # print ('阳历' + yun.getStartSolar().toYmd() + '后起运')
        if coin_data:
            coin_quote = coin_data['quote']['USD']
            # 打印比特币信息
            print(f"名称: {coin_data['name']} (符号: {coin_data['symbol']})")
            print(f"价格: ${coin_quote['price']:.2f}")
            print(f"24小时交易量: ${coin_quote['volume_24h']:.2f}")
            print(f"市值: ${coin_quote['market_cap']:.2f}")
            print(f"1小时内价格变化百分比: {coin_quote['percent_change_1h']:.2f}%")
            print(f"24小时内价格变化百分比: {coin_quote['percent_change_24h']:.2f}%")
            print(f"7天内价格变化百分比: {coin_quote['percent_change_7d']:.2f}%")
            print(f"30天内价格变化百分比: {coin_quote['percent_change_30d']:.2f}%")
            print(f"60天内价格变化百分比: {coin_quote['percent_change_60d']:.2f}%")
            print(f"90天内价格变化百分比: {coin_quote['percent_change_90d']:.2f}%")
    print("-"*120)




    print("匹配信息：")
    if name:
        print(f"""
1. 核心价值匹配：{bb}分
    此项为30分。说明：评估个人与资产的核心价值是否相合。核心价值匹配通常意味着双方在投资理念、价值观和长期发展目标等方面有较好的一致性。

2. 投资周期共振：{c}分
    此项为20分。说明：分析个人与资产的投资周期是否存在共振，如是否符合相同的投资时段或市场周期。共振的投资周期表示在资产增值和收益实现上可能相辅相成。

3. 风险偏好匹配：{yh}分
    此项为5分。说明：考察个人与资产在风险承受能力和风险偏好上是否有相合或相补性，这表示双方在投资决策和市场适应上可能存在共鸣。

4. 资产配置互补：{rh}分
    此项为25分。说明：资产配置代表个人投资组合的多元化和平衡。如果个人与资产的配置能够互补，如稳定收益与高风险高回报的结合，这预示着双方在资产管理和收益优化上的互补或和谐。

5. 流动性需求一致：{rrh}分
    此项为5分。说明：探讨个人与资产在资金流动性需求上是否形成一致性，这关系到双方在资金周转和资产流动性管理中的协调配合。

6. 综合适配度：{ez}分
    此项为15分。说明：综合考虑个人与资产在投资目标、风险偏好、资金管理等方面的相合程度，反映双方在整体投资策略和资产管理上的适配性。

7. 总分：{total_score}分
    综合评分，反映个人与资产在各项指标上的匹配度，为投资决策提供参考依据。
        """)
    else:    
        print(f"""
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
                """)
    # return total_score, bb, c, yh, rh, rrh, ez





# year = 2000  # 年干
# month = 5 # 月份
# day = 21  # 日
# t_ime = 5 # 时
# year_a = 1999  # 年干
# month_a = 5 # 月份
# day_a = 16  # 日
# t_ime_a = 20 # 时
# res = baziMatch(2000,5,5,8,2000,5,14,10)
# print(res)
# res = baziMatch(2000,5,5,8,2000,5,14,10,name="BTC")
# print(res)
# bazihunpei(2000,5,5,8,2000,5,14,10)  