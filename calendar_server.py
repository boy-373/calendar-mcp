"""Calendar MCP module - 万年历工具。

提供三个工具：
  1. query_holiday  - 查询指定公历日期的节假日/调休安排
  2. solar_to_lunar - 公历转农历
  3. list_holidays  - 列出指定年份全部法定节假日

数据来源：国务院办公厅发布的官方节假日安排通知。
数据年份：2025、2026（完整准确数据，可逐年扩展）。
"""

from datetime import date, timedelta
from typing import Dict, List, Optional

try:
    from fastmcp import FastMCP  # type: ignore  # fastmcp v2
except ImportError:  # pragma: no cover
    from mcp.server.fastmcp import FastMCP  # type: ignore  # fastmcp v1 (mcp sdk)

# 农历库：优先 sxtwl（C 扩展，速度快、精度高），降级到 lunardate（纯 Python）
try:
    import sxtwl as _sxtwl
    _LUNAR_BACKEND = "sxtwl"
except ImportError:
    _sxtwl = None
    try:
        from lunardate import LunarDate
        _LUNAR_BACKEND = "lunardate"
    except ImportError:
        LunarDate = None
        _LUNAR_BACKEND = "none"


# ---------------------------------------------------------------------------
# 节假日数据（国务院办公厅官方发布）
# ---------------------------------------------------------------------------
# 结构：holidays = {
#   "2025": {
#       "元旦": {"off": ["2025-01-01"], "work": []},
#       ...
#   },
#   ...
# }
# off: 放假日期列表（含调休放假）
# work: 调休上班日期列表

HOLIDAY_DATA: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "2025": {
        "元旦": {
            "off": ["2025-01-01"],
            "work": [],
        },
        "春节": {
            "off": [
                "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",
                "2025-02-01", "2025-02-02", "2025-02-03", "2025-02-04",
            ],
            "work": ["2025-01-26", "2025-02-08"],
        },
        "清明节": {
            "off": ["2025-04-04", "2025-04-05", "2025-04-06"],
            "work": [],
        },
        "劳动节": {
            "off": [
                "2025-05-01", "2025-05-02", "2025-05-03",
                "2025-05-04", "2025-05-05",
            ],
            "work": ["2025-04-27"],
        },
        "端午节": {
            "off": ["2025-05-31", "2025-06-01", "2025-06-02"],
            "work": [],
        },
        "国庆节、中秋节": {
            "off": [
                "2025-10-01", "2025-10-02", "2025-10-03", "2025-10-04",
                "2025-10-05", "2025-10-06", "2025-10-07", "2025-10-08",
            ],
            "work": ["2025-09-28", "2025-10-11"],
        },
    },
    "2026": {
        "元旦": {
            "off": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "work": ["2026-01-04"],
        },
        "春节": {
            "off": [
                "2026-02-15", "2026-02-16", "2026-02-17", "2026-02-18",
                "2026-02-19", "2026-02-20", "2026-02-21", "2026-02-22",
                "2026-02-23",
            ],
            "work": ["2026-02-14", "2026-02-28"],
        },
        "清明节": {
            "off": ["2026-04-04", "2026-04-05", "2026-04-06"],
            "work": [],
        },
        "劳动节": {
            "off": [
                "2026-05-01", "2026-05-02", "2026-05-03",
                "2026-05-04", "2026-05-05",
            ],
            "work": ["2026-05-09"],
        },
        "端午节": {
            "off": ["2026-06-19", "2026-06-20", "2026-06-21"],
            "work": [],
        },
        "中秋节": {
            "off": ["2026-09-25", "2026-09-26", "2026-09-27"],
            "work": [],
        },
        "国庆节": {
            "off": [
                "2026-10-01", "2026-10-02", "2026-10-03",
                "2026-10-04", "2026-10-05", "2026-10-06",
                "2026-10-07",
            ],
            "work": ["2026-09-20", "2026-10-10"],
        },
    },
}

# 农历日名称表
LUNAR_DAY_NAMES = [
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
]

# 农历月名称表
LUNAR_MONTH_NAMES = [
    "正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊",
]

# 十二生肖
ZODIAC_ANIMALS = [
    "鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪",
]

# 天干
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 地支
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD date string."""
    return date.fromisoformat(date_str)


def _build_date_index() -> Dict[str, dict]:
    """Build a fast lookup index: date_string -> holiday info.

    Returns:
        {"2025-01-01": {"name": "元旦", "type": "off"},
         "2025-01-26": {"name": "春节", "type": "work"},
         ...}
    """
    index: Dict[str, dict] = {}
    for year, holidays in HOLIDAY_DATA.items():
        for holiday_name, info in holidays.items():
            for d in info["off"]:
                index[d] = {"name": holiday_name, "type": "off"}
            for d in info["work"]:
                index[d] = {"name": holiday_name, "type": "work"}
    return index


DATE_INDEX = _build_date_index()


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def query_holiday_info(date_str: str) -> dict:
    """查询指定公历日期的节假日/调休信息。

    Args:
        date_str: 日期，格式 YYYY-MM-DD

    Returns:
        包含日期、节假日名称、类型（放假/调休上班/工作日）、农历信息的字典
    """
    d = _parse_date(date_str)
    date_key = d.isoformat()
    year_str = str(d.year)

    result = {
        "date": date_key,
        "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d.weekday()],
    }

    # 查找节假日信息
    if date_key in DATE_INDEX:
        info = DATE_INDEX[date_key]
        result["holiday_name"] = info["name"]
        result["type"] = "放假" if info["type"] == "off" else "调休上班"
        result["is_holiday"] = info["type"] == "off"
        result["is_workday_adjusted"] = info["type"] == "work"
    else:
        result["holiday_name"] = None
        result["type"] = "工作日" if d.weekday() < 5 else "周末休息日"
        result["is_holiday"] = False
        result["is_workday_adjusted"] = False

    # 附加农历信息
    lunar_info = solar_to_lunar_convert(d.year, d.month, d.day)
    result["lunar"] = lunar_info

    # 提示数据范围
    if year_str not in HOLIDAY_DATA:
        result["note"] = f"当前仅支持 {', '.join(sorted(HOLIDAY_DATA.keys()))} 年的法定节假日数据"

    return result


def solar_to_lunar_convert(year: int, month: int, day: int) -> dict:
    """公历转农历。

    Args:
        year: 公历年
        month: 公历月
        day: 公历日

    Returns:
        包含农历年、月、日、是否闰月、生肖、干支等信息的字典
    """
    if _LUNAR_BACKEND == "sxtwl":
        return _solar_to_lunar_sxtwl(year, month, day)
    elif _LUNAR_BACKEND == "lunardate":
        return _solar_to_lunar_lunardate(year, month, day)
    else:
        raise RuntimeError("无可用农历转换库（sxtwl 和 lunardate 均未安装）")


def _solar_to_lunar_sxtwl(year: int, month: int, day: int) -> dict:
    """sxtwl 后端的公历转农历。"""
    lunar = _sxtwl.fromSolar(year, month, day)

    lunar_year = lunar.getLunarYear()
    lunar_month = lunar.getLunarMonth()
    lunar_day = lunar.getLunarDay()
    is_leap = lunar.isLunarLeap()

    # 月名称
    if lunar_month < 0:
        # 闰月（sxtwl 返回负数表示闰月）
        month_idx = abs(lunar_month) - 1
        month_name = f"闰{LUNAR_MONTH_NAMES[month_idx]}月"
    else:
        month_idx = lunar_month - 1
        month_name = f"{LUNAR_MONTH_NAMES[month_idx]}月"

    # 日名称
    day_name = LUNAR_DAY_NAMES[lunar_day - 1]

    # 生肖
    zodiac = ZODIAC_ANIMALS[(lunar_year - 4) % 12]

    # 年干支
    year_gz = lunar.getYearGZ()
    year_ganzhi = TIAN_GAN[year_gz.tg] + DI_ZHI[year_gz.dz]

    # 月干支
    month_gz = lunar.getMonthGZ()
    month_ganzhi = TIAN_GAN[month_gz.tg] + DI_ZHI[month_gz.dz]

    # 日干支
    day_gz = lunar.getDayGZ()
    day_ganzhi = TIAN_GAN[day_gz.tg] + DI_ZHI[day_gz.dz]

    return {
        "lunar_year": lunar_year,
        "lunar_month": abs(lunar_month),
        "lunar_day": lunar_day,
        "is_leap_month": is_leap,
        "lunar_date_str": f"{lunar_year}年{month_name}{day_name}",
        "zodiac": zodiac,
        "year_ganzhi": year_ganzhi,
        "month_ganzhi": month_ganzhi,
        "day_ganzhi": day_ganzhi,
        "solar_date": f"{year}-{month:02d}-{day:02d}",
    }


def _solar_to_lunar_lunardate(year: int, month: int, day: int) -> dict:
    """lunardate（纯 Python）后端的公历转农历。"""
    lunar = LunarDate.fromSolarDate(year, month, day)

    lunar_year = lunar.year
    lunar_month = lunar.month
    lunar_day = lunar.day
    is_leap = lunar.isLeapMonth

    # 月名称
    month_idx = abs(lunar_month) - 1
    if is_leap:
        month_name = f"闰{LUNAR_MONTH_NAMES[month_idx]}月"
    else:
        month_name = f"{LUNAR_MONTH_NAMES[month_idx]}月"

    # 日名称
    day_name = LUNAR_DAY_NAMES[lunar_day - 1]

    # 生肖
    zodiac = ZODIAC_ANIMALS[(lunar_year - 4) % 12]

    # 干支计算（简化版，基于年份推算）
    # 年干支
    year_ganzhi = TIAN_GAN[(lunar_year - 4) % 10] + DI_ZHI[(lunar_year - 4) % 12]

    # 月干支（简化：基于农历月，正月起寅）
    # 年干决定正月天干：甲己之年丙作首，乙庚之年戊为头，丙辛之岁寻庚起，丁壬壬寅顺水流，戊癸何方发，甲寅之上好追求
    year_tian_gan_idx = (lunar_year - 4) % 10
    first_month_gan_map = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]  # 丙戊庚壬甲 循环
    first_month_gan = first_month_gan_map[year_tian_gan_idx]
    month_gan_idx = (first_month_gan + lunar_month - 1) % 10
    month_zhi_idx = (lunar_month + 1) % 12  # 正月=寅(2)
    month_ganzhi = TIAN_GAN[month_gan_idx] + DI_ZHI[month_zhi_idx]

    # 日干支（用已知基准日推算：1900-01-01 对应甲戌日，日干支序号为10）
    from datetime import date as _date
    base = _date(1900, 1, 1)
    target = _date(year, month, day)
    delta_days = (target - base).days
    # 1900-01-01 是甲戌日：天干甲(0)，地支戌(10) → 序号基准
    day_gan_idx = (delta_days + 0) % 10  # 甲=0
    day_zhi_idx = (delta_days + 10) % 12  # 戌=10
    day_ganzhi = TIAN_GAN[day_gan_idx] + DI_ZHI[day_zhi_idx]

    return {
        "lunar_year": lunar_year,
        "lunar_month": abs(lunar_month),
        "lunar_day": lunar_day,
        "is_leap_month": is_leap,
        "lunar_date_str": f"{lunar_year}年{month_name}{day_name}",
        "zodiac": zodiac,
        "year_ganzhi": year_ganzhi,
        "month_ganzhi": month_ganzhi,
        "day_ganzhi": day_ganzhi,
        "solar_date": f"{year}-{month:02d}-{day:02d}",
    }


def list_holidays_by_year(year: int) -> dict:
    """列出指定年份的全部法定节假日安排。

    Args:
        year: 年份

    Returns:
        包含各节假日名称、放假天数、放假日期范围、调休上班日期的字典
    """
    year_str = str(year)
    if year_str not in HOLIDAY_DATA:
        return {
            "year": year,
            "available_years": sorted(HOLIDAY_DATA.keys()),
            "holidays": [],
            "note": f"暂无 {year} 年的节假日数据，当前支持年份：{', '.join(sorted(HOLIDAY_DATA.keys()))}",
        }

    holidays_data = HOLIDAY_DATA[year_str]
    result_list = []
    total_off_days = 0
    total_work_adjust = 0

    for name, info in holidays_data.items():
        off_dates = sorted(info["off"])
        work_dates = sorted(info["work"])
        days_count = len(off_dates)
        total_off_days += days_count
        total_work_adjust += len(work_dates)

        # 计算日期范围字符串
        if len(off_dates) == 1:
            date_range = off_dates[0]
        else:
            date_range = f"{off_dates[0]} 至 {off_dates[-1]}"

        result_list.append({
            "name": name,
            "days": days_count,
            "date_range": date_range,
            "off_dates": off_dates,
            "work_adjust_dates": work_dates,
        })

    return {
        "year": year,
        "total_holiday_days": total_off_days,
        "total_work_adjust_days": total_work_adjust,
        "holidays": result_list,
    }


# ---------------------------------------------------------------------------
# MCP 注册
# ---------------------------------------------------------------------------

def register():
    """注册万年历 MCP 模块。

    Returns:
        (path_prefix, fastmcp_instance)
    """
    mcp = FastMCP("calendar-mcp")

    @mcp.tool(description="查询指定公历日期的中国法定节假日或调休安排，同时返回农历信息。支持2025、2026年。参数date格式：YYYY-MM-DD")
    def query_holiday(date: str) -> dict:
        """查询指定公历日期的中国法定节假日/调休安排。

        Args:
            date: 公历日期，格式 YYYY-MM-DD，如 "2026-10-01"

        Returns:
            包含日期、星期、节假日名称、类型（放假/调休上班/工作日/周末）、农历信息
        """
        return query_holiday_info(date)

    @mcp.tool(description="将公历日期转换为农历日期，返回农历年月日、是否闰月、生肖、干支等信息")
    def solar_to_lunar(year: int, month: int, day: int) -> dict:
        """公历转农历。

        Args:
            year: 公历年，如 2026
            month: 公历月，如 2
            day: 公历日，如 17

        Returns:
            包含农历年、月、日、闰月标记、生肖、干支纪年等信息
        """
        return solar_to_lunar_convert(year, month, day)

    @mcp.tool(description="列出指定年份的全部中国法定节假日安排，包括放假日期和调休上班日期。支持2025、2026年")
    def list_holidays(year: int) -> dict:
        """列出指定年份的全部法定节假日。

        Args:
            year: 年份，如 2026

        Returns:
            包含各节假日名称、天数、日期范围、调休上班日期等
        """
        return list_holidays_by_year(year)

    return "/calendar-mcp", mcp
