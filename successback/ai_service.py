# backend/ai_service.py
import json
from datetime import date, timedelta
import calendar
from chinese_calendar import is_workday
from openai import OpenAI
from models import User

# --- 配置部分 ---
# 这里以 DeepSeek 为例 (它便宜且聪明)，你也可以换成 Kimi 或 OpenAI
# 如果你暂时没有 Key，可以先去 deepseek.com 申请一个，或者用其他兼容的
API_KEY = "sk-fe094c70b3a54f9facdf844d78918ae2"  # <--- 【重点】请替换为你的 API Key
BASE_URL = "https://api.deepseek.com"      # 如果用 Kimi，改为 https://api.moonshot.cn/v1

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def get_month_dates(year: int, month: int):
    """生成当月每一天的详细信息 (日期, 是否节假日)"""
    num_days = calendar.monthrange(year, month)[1]
    days_info = []
    
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        # is_workday 返回 True 表示是工作日 (包含调休上班)，False 表示休息日
        is_holiday_or_weekend = not is_workday(current_date)
        
        days_info.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "is_holiday": is_holiday_or_weekend,
            "weekday": current_date.strftime("%A") # 星期几
        })
    return days_info

def generate_schedule_by_ai(year: int, month: int, users: list[User]):
    """调用 AI 生成排班表"""
    
    # 1. 准备数据
    days_info = get_month_dates(year, month)
    user_names = [u.real_name for u in users] # 只提取名字
    
    # 2. 编写提示词 (Prompt) - 这是最关键的一步
    # 我们要求 AI 必须返回纯 JSON，不要废话
    system_prompt = "你是一个专业的排班助手。请根据给定的日期和人员名单进行公平排班。"
    user_prompt = f"""
    任务：为 {year}年{month}月 进行排班。
    
    【可用人员名单】：
    {json.dumps(user_names, ensure_ascii=False)}
    
    【日期详情】：
    {json.dumps(days_info, ensure_ascii=False)}
    
    【排班规则】：
    1. 每天必须安排 1 个人值班。
    2. 尽量保证每个人值班天数均衡。
    3. 节假日和周末通常比较辛苦，请尽量轮换，不要让同一个人连续值班。
    
    【输出格式要求】：
    必须返回一个严格的 JSON 数组，不要包含 Markdown 格式，不要```json开头。
    数组中每个对象包含两个字段：
    - "date": "YYYY-MM-DD"
    - "staff": "姓名"
    """

    try:
        # 3. 调用 AI
        response = client.chat.completions.create(
            model="deepseek-chat", # 或者 "moonshot-v1-8k", "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, # 温度低一点，让它更理性、格式更稳定
            response_format={ "type": "json_object" } # 强制 JSON (部分模型支持)
        )
        
        content = response.choices[0].message.content
        # 清洗数据：有时候 AI 会带上 ```json ... ```，我们需要去掉
        if "```" in content:
            content = content.replace("```json", "").replace("```", "")
            
        schedule_data = json.loads(content)
        
        # 兼容处理：有些 AI 返回 {"schedule": [...]}，有些直接返回 [...]
        if isinstance(schedule_data, dict):
            # 尝试找列表字段
            for key in schedule_data:
                if isinstance(schedule_data[key], list):
                    return schedule_data[key]
        return schedule_data

    except Exception as e:
        print(f"AI 排班出错: {e}")
        return []
