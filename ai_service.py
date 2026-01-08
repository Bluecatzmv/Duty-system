import json
from datetime import date
import calendar
from chinese_calendar import is_workday
from openai import OpenAI
from models import User, DutyType

# 请填入你的 Key
API_KEY = "sk-d1d74cfc38734d039fb3abcbf8eddef4" 
BASE_URL = "https://api.deepseek.com"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def get_month_dates(year: int, month: int):
    num_days = calendar.monthrange(year, month)[1]
    days_info = []
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        is_holiday_or_weekend = not is_workday(current_date)
        days_info.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "is_holiday": is_holiday_or_weekend,
            "weekday": current_date.strftime("%A")
        })
    return days_info

def generate_schedule_by_ai(year: int, month: int, users: list[User]):
    """AI 排班：只负责【技术值班】"""
    
    days_info = get_month_dates(year, month)
    
    # 只提取能做“技术值班”的人
    # 注意：如果某人既能做技术又能做别的，只要他标记了 TECH 就可以进池子
    techs = [u.real_name for u in users if u.can_do_duty == DutyType.TECH]

    if not techs:
        print("错误：没有找到技术值班人员")
        return None

    system_prompt = "你是一个排班助手。请只为【技术值班】岗位进行排班。"
    
    user_prompt = f"""
    任务：为 {year}年{month}月 进行技术值班排班。
    
    【可用技术人员名单】：
    {json.dumps(techs, ensure_ascii=False)}
    
    【日期详情】：
    {json.dumps(days_info, ensure_ascii=False)}
    
    【排班规则】：
    1. 每天安排 1 名技术值班人员。
    2. 尽量保证每个人值班天数均衡。
    3. 避免同一个人连续值班。
    
    【输出格式要求】：
    返回一个 JSON 数组，数组中每个对象包含：
    - "date": "YYYY-MM-DD"
    - "staff": "姓名"
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content
        if "```" in content:
            content = content.replace("```json", "").replace("```", "")
            
        data = json.loads(content)
        
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list):
                    return data[key]
        return data

    except Exception as e:
        print(f"AI 排班出错: {e}")
        return []
