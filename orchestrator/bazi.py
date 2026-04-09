"""
八字分析引擎 v2（基于sxtwl）
使用sxtwl库进行精确排盘，支持节气分界、大运流年计算
"""

from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import sxtwl

# ============ 基础数据 ============

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

WUXING_TG = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}

WUXING_DZ = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

# 地支藏干表（本气+中气+余气）
CANGGAN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

WUXING_NAMES = ["木", "火", "土", "金", "水"]

JQ_NAMES = [
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪"
]


# ============ 核心排盘函数 ============

def gz_str(gz) -> str:
    """天干地支对象转字符串"""
    return f"{TIANGAN[gz.tg]}{DIZHI[gz.dz]}"


def get_bazi(solar_year: int, solar_month: int, solar_day: int, hour: int) -> Dict:
    """
    精确排八字
    
    Args:
        solar_year/month/day: 阳历出生日期
        hour: 出生小时（24小时制）
    
    Returns:
        八字字典，包含年月日时四柱和详细信息
    """
    day = sxtwl.Day.fromSolar(solar_year, solar_month, solar_day)
    
    year_gz = day.getYearGZ()
    month_gz = day.getMonthGZ()
    day_gz = day.getDayGZ()
    hour_gz = day.getHourGZ(hour)
    
    result = {
        # 四柱字符串
        "year": gz_str(year_gz),
        "month": gz_str(month_gz),
        "day": gz_str(day_gz),
        "hour": gz_str(hour_gz),
        
        # 日主信息
        "day_gan": TIANGAN[day_gz.tg],
        "day_zhi": DIZHI[day_gz.dz],
        "day_gan_wuxing": WUXING_TG[TIANGAN[day_gz.tg]],
        
        # 月令
        "month_gan": TIANGAN[month_gz.tg],
        "month_zhi": DIZHI[month_gz.dz],
        "month_gan_wuxing": WUXING_TG[TIANGAN[month_gz.tg]],
        "month_zhi_wuxing": WUXING_DZ[DIZHI[month_gz.dz]],
        
        # 年柱
        "year_gan": TIANGAN[year_gz.tg],
        "year_zhi": DIZHI[year_gz.dz],
        
        # 时柱
        "hour_gan": TIANGAN[hour_gz.tg],
        "hour_zhi": DIZHI[hour_gz.dz],
        
        # 节气信息
        "jieqi": get_jieqi_info(solar_year, solar_month, solar_day),
        
        # 出生日期
        "birth_date": f"{solar_year}-{solar_month:02d}-{solar_day:02d}",
        "birth_hour": hour,
    }
    
    # 五行计数
    result["wuxing_count"] = count_wuxing(result)
    
    # 用神忌神
    result["yongshen"], result["jishen"] = get_yongshen_jishen(result)
    
    return result


def count_wuxing(bazi: Dict) -> Dict:
    """
    统计八字五行数量（含藏干）
    天干：每个柱1个天干，计1次
    地支：统计本气 + 藏干，天地双全但主次有别
    """
    wuxing = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    
    # 天干五行（每个天干计1次）
    for g in [bazi["year_gan"], bazi["month_gan"], bazi["day_gan"], bazi["hour_gan"]]:
        wuxing[WUXING_TG[g]] += 1
    
    # 地支五行（含本气 + 藏干）
    for z in [bazi["year_zhi"], bazi["month_zhi"], bazi["day_zhi"], bazi["hour_zhi"]]:
        # 本气
        wuxing[WUXING_DZ[z]] += 1
        # 藏干
        for cg in CANGGAN.get(z, []):
            wuxing[WUXING_TG[cg]] += 1
    
    return wuxing


def get_jieqi_info(year: int, month: int, day: int) -> Dict:
    """
    获取节气信息（前后节气名称）
    """
    year_jqs = _get_year_jieqi_list(year)
    current_md = (month, day)
    
    prev_name = None
    next_name = None
    
    for i, ((m, d), jq_name) in enumerate(year_jqs):
        if (m, d) < current_md:
            prev_name = jq_name
        elif (m, d) > current_md and next_name is None:
            next_name = jq_name
            break
    
    return {"prev": prev_name, "next": next_name}


def _get_year_jieqi_list(year: int) -> List[Tuple[Tuple[int, int], str]]:
    """
    获取一年所有节气[(月日, 名称)]，内部使用
    """
    result = []
    for m in range(1, 13):
        for d in range(1, 32):
            try:
                dd = sxtwl.Day.fromSolar(year, m, d)
                if dd.hasJieQi():
                    result.append(((m, d), None))
            except:
                break
    
    result.sort(key=lambda x: x[0])
    for i, (md, _) in enumerate(result):
        result[i] = (md, JQ_NAMES[i % 24])
    
    return result


def get_yongshen_jishen(bazi: Dict) -> Tuple[List[str], List[str]]:
    """
    根据命局判断用神忌神
    简化版：辛金日主，金旺土重，用神为水木，忌神为土金
    """
    day_gan = bazi["day_gan"]
    day_zhi = bazi["day_zhi"]
    wuxing = bazi["wuxing_count"]
    
    # 简单规则（实际需要结合格局、调候等复杂判断）
    # 辛金日主，身旺，金多土重，用神水木，忌神土金
    if day_gan == "辛":
        if wuxing["金"] >= 3 and wuxing["土"] >= 2:
            return (["水", "木"], ["土", "金"])
        elif wuxing["火"] >= 3:
            return (["土", "金"], ["火", "水"])
        else:
            return (["水", "木"], ["土", "金"])
    
    # 其他日主的简化规则...
    return (["水", "木"], ["土", "金"])


# ============ 大运计算 ============

def _datetime_to_jd(dt: datetime) -> float:
    """datetime转儒略日"""
    return dt.toordinal() + 1721424.5 + (dt.hour + dt.minute / 60) / 24


def calculate_dayuyun(bazi: Dict, birth_year: int) -> List[Dict]:
    """
    计算大运
    规则：
    - 阳干（甲丙戊庚壬）顺行，阴干（乙丁己辛癸）逆行
    - 从月柱出发，数到下一个（阳顺）或前一个（阴逆）节气
    - 每3天=1岁（近似）
    """
    day_gan = bazi["day_gan"]
    month_zhi = bazi["month_zhi"]
    
    # 解析出生日期时间
    birth_date_parts = bazi["birth_date"].split("-")
    birth_month = int(birth_date_parts[1])
    birth_day = int(birth_date_parts[2])
    birth_hour = bazi["birth_hour"]
    
    day_obj = sxtwl.Day.fromSolar(birth_year, birth_month, birth_day)
    
    # 用datetime计算出生JD（getJieQiJD对非节气日返回0）
    birth_dt = datetime(birth_year, birth_month, birth_day, birth_hour)
    birth_jd = _datetime_to_jd(birth_dt)
    
    # 找前后节气JD
    prev_jd = None
    next_jd = None
    
    for i in range(1, 60):
        dd = day_obj.before(i)
        if dd.hasJieQi():
            prev_jd = dd.getJieQiJD()
            break
    
    for i in range(1, 60):
        dd = day_obj.after(i)
        if dd.hasJieQi():
            next_jd = dd.getJieQiJD()
            break
    
    is_yin_gan = day_gan in ["乙", "丁", "己", "辛", "癸"]
    direction = -1 if is_yin_gan else 1
    
    # 计算起运年龄
    if is_yin_gan:
        days = (birth_jd - prev_jd) if prev_jd else 7.5
    else:
        days = (next_jd - birth_jd) if next_jd else 7.5
    
    start_age = max(1, int(round(days / 3.0)))
    
    # 生成10步大运
    month_zhi_idx = DIZHI.index(month_zhi)
    gan_idx = TIANGAN.index(day_gan)
    
    dayun = []
    for i in range(10):
        dz_idx = (month_zhi_idx + direction * (i + 1)) % 12
        g_idx = (gan_idx + direction * (i + 1)) % 10
        age = start_age + i * 10
        
        dayun.append({
            "ganzhi": f"{TIANGAN[g_idx]}{DIZHI[dz_idx]}",
            "gan": TIANGAN[g_idx],
            "zhi": DIZHI[dz_idx],
            "age_start": age,
            "age_end": age + 9,
            "year_start": birth_year + age,
        })
    
    return dayun


def get_current_dayuyun(bazi: Dict, birth_year: int, target_year: int) -> Dict:
    """获取当前/指定年份的大运"""
    dayun_list = calculate_dayuyun(bazi, birth_year)
    
    for d in dayun_list:
        if d["year_start"] <= target_year <= d["year_start"] + 9:
            return d
    
    return dayun_list[-1] if dayun_list else None


# ============ 流年计算 ============

def get_liunian(bazi_year_gan: str, bazi_year_zhi: str, target_year: int, base_year: int) -> str:
    """
    计算流年干支
    
    Args:
        bazi_year_gan: 出生年柱天干
        bazi_year_zhi: 出生年柱地支
        target_year: 目标年份
        base_year: 基准年份（用于计算）
    """
    year_diff = target_year - base_year
    gan_idx = (TIANGAN.index(bazi_year_gan) + year_diff) % 10
    zhi_idx = (DIZHI.index(bazi_year_zhi) + year_diff) % 12
    return f"{TIANGAN[gan_idx]}{DIZHI[zhi_idx]}"


def get_year_pan(bazi: Dict, target_year: int) -> Dict:
    """
    获取流年盘（年柱+大运+流年+生肖运势）
    """
    birth_year = int(bazi["birth_date"].split("-")[0])
    dayun = get_current_dayuyun(bazi, birth_year, target_year)
    liunian = get_liunian(bazi["year_gan"], bazi["year_zhi"], target_year, birth_year)
    
    return {
        "year": target_year,
        "liunian": liunian,
        "liunian_gan": liunian[0],
        "liunian_zhi": liunian[1],
        "dayun": dayun["ganzhi"] if dayun else None,
        "age": target_year - birth_year,
    }


# ============ 五行分析 ============

def analyze_wuxing_status(bazi: Dict, season: str = None) -> Dict:
    """
    分析当前五行状态
    
    Args:
        bazi: 八字字典
        season: 当前季节（春夏秋冬/四季末），默认自动计算
    """
    if season is None:
        month = datetime.now().month
        if month == 3:
            season = "四季末"  # 辰月
        elif month == 6:
            season = "四季末"  # 未月
        elif month == 9:
            season = "四季末"  # 戌月
        elif month == 12:
            season = "四季末"  # 丑月
        elif month in [1, 2]:
            season = "冬"
        elif month in [4, 5]:
            season = "春"
        elif month in [7, 8]:
            season = "夏"
        else:  # 10, 11
            season = "秋"
    
    # 旺相休囚死表
    WUXING_STRENGTH = {
        "木": {"春": "旺", "夏": "相", "秋": "死", "冬": "休", "四季末": "囚"},
        "火": {"春": "死", "夏": "旺", "秋": "相", "冬": "囚", "四季末": "休"},
        "土": {"春": "囚", "夏": "死", "秋": "旺", "冬": "相", "四季末": "旺"},
        "金": {"春": "休", "夏": "囚", "秋": "旺", "冬": "死", "四季末": "相"},
        "水": {"春": "相", "夏": "休", "秋": "囚", "冬": "旺", "四季末": "死"}
    }
    
    yongshen = bazi["yongshen"]
    jishen = bazi["jishen"]
    wuxing = bazi["wuxing_count"]
    
    # 用神状态
    yongshen_status = {}
    for w in yongshen:
        strength = WUXING_STRENGTH[w][season]
        yongshen_status[w] = {
            "strength": strength,
            "in_bazi": wuxing.get(w, 0),
            "is_favorable": strength in ["旺", "相"]
        }
    
    # 忌神状态
    jishen_status = {}
    for w in jishen:
        strength = WUXING_STRENGTH[w][season]
        jishen_status[w] = {
            "strength": strength,
            "in_bazi": wuxing.get(w, 0),
            "is_harmful": strength in ["旺", "相"]
        }
    
    return {
        "season": season,
        "yongshen_status": yongshen_status,
        "jishen_status": jishen_status,
        "wuxing_total": wuxing,
    }


# ============ 时辰分析 ============

def get_current_shichen() -> Tuple[str, str]:
    """获取当前时辰和五行"""
    now = datetime.now()
    hour = now.hour
    
    SHICHEN_LIST = [
        (23, 1, "子时", "水"),
        (1, 3, "丑时", "土"),
        (3, 5, "寅时", "木"),
        (5, 7, "卯时", "木"),
        (7, 9, "辰时", "土"),
        (9, 11, "巳时", "火"),
        (11, 13, "午时", "火"),
        (13, 15, "未时", "土"),
        (15, 17, "申时", "金"),
        (17, 19, "酉时", "金"),
        (19, 21, "戌时", "土"),
        (21, 23, "亥时", "水"),
    ]
    
    for start, end, name, wuxing in SHICHEN_LIST:
        if start == 23:
            if hour >= start or hour < end:
                return name, wuxing
        elif start <= hour < end:
            return name, wuxing
    
    return "子时", "水"


# ============ 综合分析 ============

def get_full_analysis(bazi: Dict, target_year: int = None) -> Dict:
    """
    获取完整命局分析
    """
    if target_year is None:
        target_year = datetime.now().year
    
    birth_year = int(bazi["birth_date"].split("-")[0])
    
    return {
        "bazi": bazi,
        "dayun": calculate_dayuyun(bazi, birth_year),
        "current_dayun": get_current_dayuyun(bazi, birth_year, target_year),
        "year_pan": get_year_pan(bazi, target_year),
        "wuxing_status": analyze_wuxing_status(bazi),
        "current_shichen": get_current_shichen(),
    }


# ============ Cody Zhang 专用配置（兼容旧接口）============

CODY_BAZI_CONFIG = {
    "name": "Cody Zhang",
    "birth_year": 1993,
    "birth_month": 9,
    "birth_day": 17,
    "birth_hour": 19,
    "birth_place": "河南",
    "yongshen": ["水", "木"],
    "jishen": ["土", "金"],
}

# 兼容旧接口的常量
CODY_BAZI = {
    "year": "癸酉",
    "month": "辛酉",
    "day": "辛丑",
    "hour": "戊戌",
    "day_gan": "辛",
    "day_zhi": "丑",
}

CODY_YONGSHEN = ["水", "木"]
CODY_JISHEN = ["土", "金"]


def get_cody_bazi() -> Dict:
    """获取Cody Zhang的八字"""
    cfg = CODY_BAZI_CONFIG
    bazi = get_bazi(cfg["birth_year"], cfg["birth_month"], cfg["birth_day"], cfg["birth_hour"])
    bazi["name"] = cfg["name"]
    bazi["birth_place"] = cfg["birth_place"]
    bazi["yongshen"] = cfg["yongshen"]
    bazi["jishen"] = cfg["jishen"]
    return bazi


def get_cody_analysis(target_year: int = None) -> Dict:
    """获取Cody Zhang的完整命局分析"""
    bazi = get_cody_bazi()
    return get_full_analysis(bazi, target_year)


# ============ 兼容旧接口的便利函数 ============

def analyze_current_wuxing() -> Dict:
    """兼容旧接口：分析当前五行状态"""
    bazi = get_cody_bazi()
    return analyze_wuxing_status(bazi)


def analyze_day_luck(date_obj: date = None) -> Dict:
    """兼容旧接口：分析每日运势（基于sxtwl精确排盘）"""
    if date_obj is None:
        date_obj = date.today()
    
    bazi = get_cody_bazi()
    
    # 用sxtwl精确计算日柱
    day = sxtwl.Day.fromSolar(date_obj.year, date_obj.month, date_obj.day)
    day_gz = day.getDayGZ()
    day_gan = TIANGAN[day_gz.tg]
    day_zhi = DIZHI[day_gz.dz]
    day_wuxing = WUXING_TG[day_gan]
    
    luck_score = 0
    yongshen = CODY_YONGSHEN
    jishen = CODY_JISHEN
    
    if day_wuxing in yongshen:
        luck_score += 2
    if day_wuxing in jishen:
        luck_score -= 2
    
    day_zhi_wuxing = WUXING_DZ[day_zhi]
    if day_zhi_wuxing in yongshen:
        luck_score += 1
    if day_zhi_wuxing in jishen:
        luck_score -= 1
    
    if luck_score >= 2:
        luck_level = "大吉"
    elif luck_score >= 0:
        luck_level = "小吉"
    elif luck_score >= -1:
        luck_level = "平"
    else:
        luck_level = "凶"
    
    return {
        "date": date_obj.isoformat(),
        "day_ganzhi": f"{day_gan}{day_zhi}",
        "day_wuxing": day_wuxing,
        "luck_level": luck_level,
        "luck_score": luck_score,
    }


def get_personality_traits() -> List[str]:
    """兼容旧接口：获取性格特点分析"""
    return [
        "金旺极：性格刚硬，有主见，但容易固执",
        "辛金日主：外表柔弱，内心坚强",
        "酉金禄刃：自尊心强，不服输",
        "土为印星：重视名誉，有责任感",
        "用神水木：智慧、仁慈、流动",
        "忌神土金：过刚则折，过盛则折",
    ]


def get_current_advice() -> Dict:
    """兼容旧接口：获取当前综合建议"""
    current = analyze_current_wuxing()
    day_luck = analyze_day_luck()
    shichen_name, shichen_wuxing = get_current_shichen()
    
    # 从实际计算获取大运
    analysis = get_cody_analysis()
    dayun = analysis["current_dayun"]
    dayun_str = f"{dayun['ganzhi']}大运（{dayun['year_start']}-{dayun['year_start']+9}年）"
    
    advice = {
        "性格提醒": CODY_BAZI["day_gan"] + "金日主，性格特点：" + "；".join(get_personality_traits()[:2]),
        "今日运势": f"今日({day_luck['day_ganzhi']})：{day_luck['luck_level']}",
        "用神状态": "、".join([f"{k}({v['strength']})" for k, v in current["yongshen_status"].items()]),
        "忌神警告": "、".join([f"{k}({v['strength']})" for k, v in current["jishen_status"].items()]),
        "当前时辰": f"{shichen_name}（{shichen_wuxing}）",
        "大运": dayun_str,
    }
    
    return advice


def analyze_question(question: str) -> Dict:
    """兼容旧接口：分析用户问题类别"""
    question_lower = question.lower()
    
    keywords = {
        "工作": ["工作", "上班", "辞职", "面试", "同事", "领导"],
        "感情": ["感情", "恋爱", "婚姻", "老婆", "老公", "女朋友", "男朋友"],
        "财运": ["钱", "投资", "财运", "破财", "生意", "收入"],
        "健康": ["健康", "身体", "病", "医院", "康复"],
        "决策": ["选择", "犹豫", "决定", "怎么办", "要不要"],
    }
    
    category = "其他"
    for cat, words in keywords.items():
        if any(w in question_lower for w in words):
            category = cat
            break
    
    shichen_name, shichen_wuxing = get_current_shichen()
    
    return {
        "category": category,
        "shichen": shichen_name,
        "shichen_wuxing": shichen_wuxing,
    }


# ============ 测试 ============

if __name__ == "__main__":
    print("=== 八字排盘测试 ===")
    bazi = get_cody_bazi()
    print(f"姓名: {bazi['name']}")
    print(f"出生: {bazi['birth_date']} {bazi['birth_hour']}时")
    print(f"八字: {bazi['year']} {bazi['month']} {bazi['day']} {bazi['hour']}")
    print(f"日主: {bazi['day_gan']}{bazi['day_zhi']} ({bazi['day_gan_wuxing']}性)")
    print(f"月令: {bazi['month_gan']}{bazi['month_zhi']} ({bazi['month_zhi_wuxing']})")
    print(f"用神: {bazi['yongshen']}")
    print(f"忌神: {bazi['jishen']}")
    print(f"五行: {bazi['wuxing_count']}")
    print(f"节气: {bazi['jieqi']}")
    
    print("\n=== 大运 ===")
    dayun = calculate_dayuyun(bazi, 1993)
    for d in dayun:
        print(f"{d['age_start']}-{d['age_end']}岁: {d['ganzhi']} ({d['year_start']}-{d['year_start']+9}年)")
    
    print("\n=== 2026年盘 ===")
    analysis = get_cody_analysis(2026)
    print(f"流年: {analysis['year_pan']['liunian']}")
    print(f"大运: {analysis['year_pan']['dayun']}")
    print(f"年龄: {analysis['year_pan']['age']}岁")
    print(f"当前大运: {analysis['current_dayun']}")
    
    print("\n=== 五行状态 ===")
    ws = analysis["wuxing_status"]
    print(f"季节: {ws['season']}")
    print(f"用神状态: {ws['yongshen_status']}")
    print(f"忌神状态: {ws['jishen_status']}")
    
    print("\n=== 旧接口兼容测试 ===")
    print(analyze_current_wuxing())
    print(analyze_day_luck())
    print(get_current_advice())
