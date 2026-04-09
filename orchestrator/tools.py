"""
八字工具集 - 基于完整八字排盘系统

集成 sxtwl 精确计算：
- 八字排盘
- 大运计算
- 流年分析
- 五行状态
- 用神忌神
"""
import os
import sys

# 确保可以导入 bazi 模块
sys.path.insert(0, os.path.dirname(__file__))

from .bazi import (
    get_bazi,
    calculate_dayuyun,
    get_current_dayuyun,
    get_liunian,
    get_year_pan,
    analyze_wuxing_status,
    get_full_analysis,
    get_cody_bazi,
    get_cody_analysis,
    analyze_day_luck,
    TIANGAN,
    DIZHI,
    WUXING_TG,
    WUXING_DZ,
)
import json
from datetime import datetime


def bazi_calculation(birth_date: str, birth_time: str = "00:00") -> str:
    """
    根据出生日期计算完整八字命盘
    
    Args:
        birth_date: 出生日期 YYYY-MM-DD
        birth_time: 出生时间 HH:MM
    """
    try:
        # 解析日期
        parts = birth_date.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        
        # 解析时间
        time_parts = birth_time.split(":")
        hour = int(time_parts[0])
        
        # 计算八字
        bazi = get_bazi(year, month, day, hour)
        
        # 格式化输出
        output = {
            "birth": f"{birth_date} {birth_time}",
            "bazi": {
                "year": bazi["year"],
                "month": bazi["month"],
                "day": bazi["day"],
                "hour": bazi["hour"]
            },
            "day_master": {
                "gan": bazi["day_gan"],
                "zhi": bazi["day_zhi"],
                "wuxing": bazi["day_gan_wuxing"]
            },
            "month_ling": {
                "gan": bazi["month_gan"],
                "zhi": bazi["month_zhi"],
                "zhi_wuxing": bazi["month_zhi_wuxing"]
            },
            "wuxing_count": bazi["wuxing_count"],
            "yongshen": bazi["yongshen"],
            "jishen": bazi["jishen"],
            "jieqi": bazi["jieqi"]
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"八字计算失败: {str(e)}"}, ensure_ascii=False)


def dayun_calculation(birth_date: str, birth_time: str = "00:00", target_year: int = None) -> str:
    """
    计算大运
    
    Args:
        birth_date: 出生日期 YYYY-MM-DD
        birth_time: 出生时间 HH:MM
        target_year: 目标年份（默认当前年份）
    """
    try:
        parts = birth_date.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        time_parts = birth_time.split(":")
        hour = int(time_parts[0])
        
        bazi = get_bazi(year, month, day, hour)
        
        if target_year is None:
            target_year = datetime.now().year
        
        # 计算大运
        dayun_list = calculate_dayuyun(bazi, year)
        current_dayun = get_current_dayuyun(bazi, year, target_year)
        
        output = {
            "birth": f"{birth_date} {birth_time}",
            "target_year": target_year,
            "dayun": [
                {
                    "ganzhi": d["ganzhi"],
                    "age_start": d["age_start"],
                    "age_end": d["age_end"],
                    "year_start": d["year_start"]
                }
                for d in dayun_list
            ],
            "current_dayun": {
                "ganzhi": current_dayun["ganzhi"],
                "age_start": current_dayun["age_start"],
                "age_end": current_dayun["age_end"],
                "year_start": current_dayun["year_start"]
            } if current_dayun else None
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"大运计算失败: {str(e)}"}, ensure_ascii=False)


def fortune_reading(bazi: str = None, date: str = None, birth_date: str = None, birth_time: str = "00:00") -> str:
    """
    解读八字运势
    
    支持两种模式：
    1. 直接输入八字：fortune_reading(bazi="癸酉 辛酉 辛丑 戊戌", date="2026-04-08")
    2. 输入出生日期：fortune_reading(birth_date="1993-09-17", birth_time="19:30", date="2026-04-08")
    """
    try:
        # 模式1：直接输入八字
        if bazi and date:
            parts = bazi.split()
            if len(parts) >= 4:
                year_gan, year_zhi = parts[0][0], parts[0][1]
            else:
                return json.dumps({"error": "八字格式错误，需要年柱、月柱、日柱、时柱"}, ensure_ascii=False)
            
            target_year = int(date.split("-")[0])
            liunian = get_liunian(year_gan, year_zhi, target_year, target_year)
            
            # 获取五行分析
            bazi_data = get_cody_bazi()
            wuxing_status = analyze_wuxing_status(bazi_data)
            
            output = {
                "input_bazi": bazi,
                "date": date,
                "liunian": liunian,
                "liunian_gan": liunian[0],
                "liunian_zhi": liunian[1],
                "wuxing_status": wuxing_status
            }
            return json.dumps(output, ensure_ascii=False, indent=2)
        
        # 模式2：输入出生日期
        if birth_date:
            parts = birth_date.split("-")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            time_parts = birth_time.split(":")
            hour = int(time_parts[0])
            
            bazi_data = get_bazi(year, month, day, hour)
            
            if date:
                target_year = int(date.split("-")[0])
            else:
                target_year = datetime.now().year
            
            # 完整分析
            analysis = get_full_analysis(bazi_data, target_year)
            
            output = {
                "birth": f"{birth_date} {birth_time}",
                "bazi": {
                    "year": bazi_data["year"],
                    "month": bazi_data["month"],
                    "day": bazi_data["day"],
                    "hour": bazi_data["hour"]
                },
                "yongshen": bazi_data["yongshen"],
                "jishen": bazi_data["jishen"],
                "year_pan": analysis["year_pan"],
                "current_dayun": {
                    "ganzhi": analysis["current_dayun"]["ganzhi"],
                    "age_start": analysis["current_dayun"]["age_start"],
                    "year_start": analysis["current_dayun"]["year_start"]
                } if analysis.get("current_dayun") else None,
                "wuxing_status": analysis["wuxing_status"],
                "current_shichen": analysis["current_shichen"]
            }
            return json.dumps(output, ensure_ascii=False, indent=2)
        
        return json.dumps({"error": "参数不足，需要提供 bazi 或 birth_date"}, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"运势解读失败: {str(e)}"}, ensure_ascii=False)


def five_elements_analysis(bazi: str = None, birth_date: str = None, birth_time: str = "00:00") -> str:
    """
    五行旺衰分析
    
    Args:
        bazi: 八字字符串 (如 "癸酉 辛酉 辛丑 戊戌")
        birth_date: 出生日期 (二选一)
        birth_time: 出生时间
    """
    try:
        if birth_date:
            parts = birth_date.split("-")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            time_parts = birth_time.split(":")
            hour = int(time_parts[0])
            bazi_data = get_bazi(year, month, day, hour)
        elif bazi:
            # 从八字字符串解析（简化版）
            parts = bazi.split()
            if len(parts) >= 4:
                # 这里用简化逻辑
                bazi_data = {
                    "wuxing_count": {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
                }
                for p in parts:
                    if len(p) >= 2:
                        gan, zhi = p[0], p[1]
                        if gan in WUXING_TG:
                            bazi_data["wuxing_count"][WUXING_TG[gan]] += 1
                        if zhi in WUXING_DZ:
                            bazi_data["wuxing_count"][WUXING_DZ[zhi]] += 1
            else:
                return json.dumps({"error": "八字格式错误"}, ensure_ascii=False)
        else:
            return json.dumps({"error": "参数不足"}, ensure_ascii=False)
        
        # 五行分析
        wuxing = bazi_data["wuxing_count"]
        total = sum(wuxing.values())
        
        # 找出最旺和最弱的五行
        sorted_wuxing = sorted(wuxing.items(), key=lambda x: x[1], reverse=True)
        
        output = {
            "source": "birth_date" if birth_date else "bazi",
            "wuxing_count": wuxing,
            "total": total,
            "percentage": {k: round(v/total*100, 1) if total > 0 else 0 for k, v in wuxing.items()},
            "strongest": sorted_wuxing[0][0] if sorted_wuxing else None,
            "weakest": sorted_wuxing[-1][0] if sorted_wuxing else None,
            "balanced": "较平衡" if max(wuxing.values()) - min(wuxing.values()) <= 3 else "不平衡"
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"五行分析失败: {str(e)}"}, ensure_ascii=False)


def daily_fortune(date: str = None) -> str:
    """
    每日运势分析（基于Cody的八字）
    
    Args:
        date: 日期 YYYY-MM-DD（默认今天）
    """
    try:
        if date is None:
            from datetime import date as date_type
            date = date_type.today().isoformat()
        
        result = analyze_day_luck(datetime.strptime(date, "%Y-%m-%d").date())
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"每日运势分析失败: {str(e)}"}, ensure_ascii=False)


def full_analysis(birth_date: str, birth_time: str = "00:00", target_year: int = None) -> str:
    """
    完整命局分析（八字+大运+流年+五行+建议）
    
    Args:
        birth_date: 出生日期 YYYY-MM-DD
        birth_time: 出生时间 HH:MM
        target_year: 目标年份（默认今年）
    """
    try:
        parts = birth_date.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        time_parts = birth_time.split(":")
        hour = int(time_parts[0])
        
        bazi_data = get_bazi(year, month, day, hour)
        
        if target_year is None:
            target_year = datetime.now().year
        
        analysis = get_full_analysis(bazi_data, target_year)
        
        output = {
            "birth": f"{birth_date} {birth_time}",
            "bazi": {
                "year": bazi_data["year"],
                "month": bazi_data["month"],
                "day": bazi_data["day"],
                "hour": bazi_data["hour"]
            },
            "day_master": {
                "gan": bazi_data["day_gan"],
                "zhi": bazi_data["day_zhi"],
                "wuxing": bazi_data["day_gan_wuxing"]
            },
            "yongshen": bazi_data["yongshen"],
            "jishen": bazi_data["jishen"],
            "wuxing_count": bazi_data["wuxing_count"],
            "jieqi": bazi_data["jieqi"],
            "dayun": analysis["dayun"],
            "current_dayun": analysis["current_dayun"],
            "year_pan": analysis["year_pan"],
            "wuxing_status": analysis["wuxing_status"],
            "current_shichen": analysis["current_shichen"]
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"完整分析失败: {str(e)}"}, ensure_ascii=False)


# ============================================================
# 扩展工具集 - 通用能力
# ============================================================

def _init_general_tools():
    """初始化通用工具"""
    import json
    import re
    import math
    from datetime import datetime, timedelta
    from urllib.request import urlopen, Request
    from urllib.error import URLError
    
    # === 网络搜索 ===
    def web_search(query: str, limit: int = 5) -> str:
        """网络搜索（使用 DuckDuckGo）"""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=limit))
            if not results:
                return "未找到相关结果"
            
            output = []
            for i, r in enumerate(results, 1):
                output.append(f"{i}. {r['title']}")
                output.append(f"   {r['href']}")
                if r.get('body'):
                    output.append(f"   {r['body'][:150]}...")
                output.append("")
            return "\n".join(output)
        except ImportError:
            return "需要安装 duckduckgo-search: pip install duckduckgo-search"
        except Exception as e:
            return f"搜索失败: {str(e)}"
    
    # === URL 内容获取 ===
    def fetch_url(url: str, timeout: int = 10) -> str:
        """获取 URL 内容"""
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8', errors='ignore')
                # 简单清理 HTML
                text = re.sub(r'<[^>]+>', ' ', content)
                text = re.sub(r'\s+', ' ', text)
                return text[:3000] + "..." if len(text) > 3000 else text
        except URLError as e:
            return f"获取失败: {str(e)}"
        except Exception as e:
            return f"错误: {str(e)}"
    
    # === JSON 格式化/解析 ===
    def json_format(json_str: str, indent: int = 2) -> str:
        """格式化 JSON 字符串"""
        try:
            obj = json.loads(json_str)
            return json.dumps(obj, indent=indent, ensure_ascii=False)
        except json.JSONDecodeError as e:
            return f"JSON 解析错误: {str(e)}"
    
    def json_query(json_str: str, path: str) -> str:
        """JSONPath 查询（简化版）"""
        try:
            obj = json.loads(json_str)
            # 简单点号路径
            for key in path.split('.'):
                if key.isdigit() and isinstance(obj, list):
                    obj = obj[int(key)]
                elif isinstance(obj, dict):
                    obj = obj.get(key, None)
                else:
                    return f"路径不存在: {path}"
            return json.dumps(obj, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"查询失败: {str(e)}"
    
    # === 计算器 ===
    def calculate(expression: str) -> str:
        """安全数学计算"""
        try:
            # 只允许数字和基本运算符
            if not re.match(r'^[\d\s+\-*/().]+$', expression):
                return "只支持数字和 + - * / () 运算符"
            result = eval(expression)
            return f"{expression} = {result}"
        except ZeroDivisionError:
            return "错误: 除数不能为零"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    # === 日期时间 ===
    def date_now(format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """当前日期时间"""
        return datetime.now().strftime(format)
    
    def date_calc(date_str: str, days: int, format: str = "%Y-%m-%d") -> str:
        """日期计算（加减天数）"""
        try:
            d = datetime.strptime(date_str, format)
            result = d + timedelta(days=days)
            return result.strftime(format)
        except ValueError as e:
            return f"日期格式错误: {str(e)}"
    
    def date_diff(date1: str, date2: str, format: str = "%Y-%m-%d") -> str:
        """计算两个日期的差值"""
        try:
            d1 = datetime.strptime(date1, format)
            d2 = datetime.strptime(date2, format)
            diff = abs((d2 - d1).days)
            return f"相差 {diff} 天"
        except ValueError as e:
            return f"日期格式错误: {str(e)}"
    
    # === 文本处理 ===
    def text_count(text: str, pattern: str) -> str:
        """统计文本中模式出现的次数"""
        try:
            count = len(re.findall(pattern, text))
            return f"'{pattern}' 出现 {count} 次"
        except Exception as e:
            return f"正则错误: {str(e)}"
    
    def text_replace(text: str, old: str, new: str) -> str:
        """批量文本替换"""
        return text.replace(old, new)
    
    def text_extract(text: str, pattern: str) -> str:
        """正则提取"""
        try:
            matches = re.findall(pattern, text)
            return "\n".join(matches) if matches else "未匹配"
        except Exception as e:
            return f"正则错误: {str(e)}"
    
    # === 编码转换 ===
    def encode_base64(text: str) -> str:
        """Base64 编码"""
        import base64
        return base64.b64encode(text.encode()).decode()
    
    def decode_base64(encoded: str) -> str:
        """Base64 解码"""
        import base64
        try:
            return base64.b64decode(encoded.encode()).decode()
        except Exception as e:
            return f"解码失败: {str(e)}"
    
    def encode_url(text: str) -> str:
        """URL 编码"""
        from urllib.parse import quote
        return quote(text)
    
    # === Hash 计算 ===
    def hash_md5(text: str) -> str:
        """MD5 哈希"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def hash_sha256(text: str) -> str:
        """SHA256 哈希"""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()
    
    # === UUID ===
    def uuid_generate(count: int = 1) -> str:
        """生成 UUID"""
        import uuid
        if count == 1:
            return str(uuid.uuid4())
        return "\n".join([str(uuid.uuid4()) for _ in range(count)])
    
    # === 密码生成 ===
    def password_generate(length: int = 16, complex: bool = True) -> str:
        """生成随机密码"""
        import random
        import string
        chars = string.ascii_letters + string.digits
        if complex:
            chars += "!@#$%^&*"
        return "".join(random.choice(chars) for _ in range(length))
    
    # 注册通用工具
    registry.register_function("web_search", web_search, "网络搜索")
    registry.register_function("fetch_url", fetch_url, "获取 URL 内容")
    registry.register_function("json_format", json_format, "格式化 JSON")
    registry.register_function("json_query", json_query, "JSONPath 查询")
    registry.register_function("calculate", calculate, "数学计算")
    registry.register_function("date_now", date_now, "当前日期时间")
    registry.register_function("date_calc", date_calc, "日期计算")
    registry.register_function("date_diff", date_diff, "日期差计算")
    registry.register_function("text_count", text_count, "文本统计")
    registry.register_function("text_replace", text_replace, "文本替换")
    registry.register_function("text_extract", text_extract, "正则提取")
    registry.register_function("encode_base64", encode_base64, "Base64 编码")
    registry.register_function("decode_base64", decode_base64, "Base64 解码")
    registry.register_function("encode_url", encode_url, "URL 编码")
    registry.register_function("hash_md5", hash_md5, "MD5 哈希")
    registry.register_function("hash_sha256", hash_sha256, "SHA256 哈希")
    registry.register_function("uuid_generate", uuid_generate, "生成 UUID")
    registry.register_function("password_generate", password_generate, "生成密码")


# 在文件末尾调用初始化
_init_general_tools()
