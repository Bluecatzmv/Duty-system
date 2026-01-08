import httpx # 新增
from apscheduler.schedulers.asyncio import AsyncIOScheduler # 新增
from apscheduler.triggers.cron import CronTrigger # 新增
# 确保导入了 date, datetime
from datetime import date # 确保导入了 date
from models import User, Role, UserRead, Schedule, ScheduleStatus, SwapRequest, RequestStatus # 导入 Schedule 模型
from ai_service import generate_schedule_by_ai # 导入刚才写的服务
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select, create_engine, SQLModel
from contextlib import asynccontextmanager
from typing import Annotated, List
import openpyxl
from io import BytesIO 
from datetime import timedelta, date, datetime

# 导入我们的模块
from models import User, Role, UserRead
from auth import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt

WECHAT_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b1660edc-cb1f-4a5f-b55a-0bdd8b58a0ac"

# 1. 数据库配置
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

# 依赖注入类型提示
SessionDep = Annotated[Session, Depends(get_session)]

# 2. 初始化数据库与默认管理员
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        admin_exist = session.exec(select(User).where(User.role == Role.ADMIN)).first()
        if not admin_exist:
            print("正在创建默认管理员账号...")
            admin_user = User(
                username="admin", 
                real_name="系统管理员",
                password_hash=get_password_hash("admin123"), 
                role=Role.ADMIN
            )
            session.add(admin_user)
            session.commit()
            print("管理员创建成功！账号: admin, 密码: admin123")


async def send_daily_reminder():
    """核心逻辑：查询今日值班并推送企业微信"""
    print(f"[{datetime.now()}] 正在检查今日值班情况...")
    
    # 1. 建立临时的数据库会话 (因为定时任务不在 HTTP 请求周期内)
    with Session(engine) as session:
        today = date.today()
        
        # 查表
        schedule = session.exec(
            select(Schedule).where(Schedule.date == today)
        ).first()
        
        if not schedule:
            print("今日无排班记录，跳过提醒。")
            return
            
        # 获取人员信息 (注意：sqlmodel 懒加载，需要手动访问一下 user 属性)
        if not schedule.user:
            # 如果 user 没加载出来，重新查一次
            user = session.get(User, schedule.user_id)
        else:
            user = schedule.user
            
        if not user:
            print("排班记录异常，找不到对应的用户。")
            return

        # 2. 构造企业微信消息 (Markdown 格式)
        # 如果用户有手机号，可以直接 <@手机号> 来提醒他
        mention_str = f"<@{user.phone}>" if user.phone else f"**{user.real_name}**"
        
        content = f"""
        # 📅 今日值班提醒
        
        > 日期：<font color=\"comment\">{today}</font>
        > 值班人员：{mention_str}
        > 部门：{user.department or '暂无'}
        
        请准时到岗，辛苦了！💪
        """
        
        # 去掉缩进带来的空格
        import textwrap
        content = textwrap.dedent(content).strip()

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        # 3. 发送请求
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(WECHAT_WEBHOOK_URL, json=payload)
                print(f"企微推送结果: {resp.text}")
            except Exception as e:
                print(f"企微推送失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 启动数据库
    create_db_and_tables()
    
    # 2. 启动定时任务调度器
    scheduler = AsyncIOScheduler()
    
    # 添加任务：每天早上 08:30 触发
    # 这里的 hour=8, minute=30 可以根据你需要调整
    scheduler.add_job(send_daily_reminder, CronTrigger(hour=8, minute=30))
    
    scheduler.start()
    print("⏰ 定时任务调度器已启动 (每天 08:30 推送)")
    
    yield
    
    # App 关闭时关闭调度器
    scheduler.shutdown()



app = FastAPI(title="AI智能值班系统 API", lifespan=lifespan)

# 定义认证方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- 辅助函数 ---

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep):
    """验证 Token 并获取当前登录的用户对象"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(current_user: Annotated[User, Depends(get_current_user)]):
    """权限锁：只允许管理员进入"""
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="权限不足，需要管理员权限")
    return current_user

# --- 接口定义 ---

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
):
    """登录接口"""
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/users/", response_model=List[UserRead])
def read_users(
    session: SessionDep, 
    current_user: User = Depends(get_current_user)
):
    """获取所有员工列表"""
    users = session.exec(select(User)).all()
    return users

@app.post("/users/import")
async def import_users(
    session: SessionDep,          # <--- 修改点：移到了第一个位置
    file: UploadFile = File(...), # <--- 有默认值的放在后面
    admin: User = Depends(get_current_admin)
):
    """Excel 批量导入员工 (仅管理员)"""
    # 检查文件格式
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="请上传 .xlsx 格式的 Excel 文件")
    
    # 读取 Excel
    contents = await file.read()
    wb = openpyxl.load_workbook(BytesIO(contents))
    sheet = wb.active 
    
    count = 0
    # 从第2行开始读取
    for row in sheet.iter_rows(min_row=2, values_only=True):
        real_name = row[0]
        username = row[1]
        department = row[2]
        phone = row[3]
        
        if not username: 
            continue
            
        existing_user = session.exec(select(User).where(User.username == username)).first()
        if existing_user:
            continue 
            
        new_user = User(
            username=str(username),
            real_name=str(real_name),
            department=str(department) if department else None,
            phone=str(phone) if phone else None,
            password_hash=get_password_hash("123456"), 
            role=Role.USER
        )
        session.add(new_user)
        count += 1
        
    session.commit()
    return {"message": f"成功导入 {count} 名员工", "status": "success"}

# --- 排班相关接口 ---

@app.post("/schedules/auto-generate")
async def auto_generate_schedule(
    year: int, 
    month: int,
    session: SessionDep,
    admin: User = Depends(get_current_admin) # 只有管理员能排班
):
    """调用 AI 自动生成排班"""
    # 1. 获取所有用户
    users = session.exec(select(User)).all()
    if not users:
        raise HTTPException(status_code=400, detail="没有员工，无法排班")

    # 2. 调用 AI 服务
    # 注意：这是一个耗时操作，生产环境最好用后台任务(Celery)，这里演示直接调用
    print(f"正在请求 AI 进行 {year}-{month} 排班...")
    ai_result = generate_schedule_by_ai(year, month, users)

    if not ai_result:
        raise HTTPException(status_code=500, detail="AI 生成失败，请检查 API Key 或重试")

    # 3. 保存到数据库
    # 先删除当月已有的排班（覆盖模式）
    # 计算当月第一天和最后一天
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    statement = select(Schedule).where(Schedule.date >= start_date).where(Schedule.date <= end_date)
    existing_schedules = session.exec(statement).all()
    for s in existing_schedules:
        session.delete(s)

    count = 0
    for item in ai_result:
        duty_date_str = item.get("date") # "2025-01-01"
        staff_name = item.get("staff")

        if not duty_date_str or not staff_name:
            continue

        # 找到对应的 User 对象
        # 简单起见，这里假设真实姓名是唯一的。如果重名，建议用 username 匹配
        staff_user = session.exec(select(User).where(User.real_name == staff_name)).first()

        if staff_user:
            duty_date = date.fromisoformat(duty_date_str)
            new_schedule = Schedule(
                date=duty_date,
                user_id=staff_user.id,
                status=ScheduleStatus.NORMAL,
                # 简单判断周末，你也可以存 AI 返回的 is_holiday
                is_holiday=(duty_date.weekday() >= 5) 
            )
            session.add(new_schedule)
            count += 1

    session.commit()
    return {"message": f"AI 排班完成！已生成 {count} 条记录", "status": "success"}

@app.get("/schedules/")
def get_schedules(
    year: int, 
    month: int,
    session: SessionDep,
    user: User = Depends(get_current_user)
):
    """获取某月的排班表"""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    # 连表查询，把 User 信息也带出来
    statement = select(Schedule).where(Schedule.date >= start_date)\
                                .where(Schedule.date <= end_date)\
                                .order_by(Schedule.date)
    results = session.exec(statement).all()
    return results

# --- 换班与审批业务 ---

@app.post("/swaps/apply")
async def create_swap_request(
    original_date: date,
    target_date: date,
    reason: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """
    员工发起换班申请
    :param original_date: 我原本值班的日期
    :param target_date: 我想换到的日期
    """
    # 1. 验证：original_date 当天必须真的是该用户值班
    sched = session.exec(
        select(Schedule)
        .where(Schedule.date == original_date)
        .where(Schedule.user_id == current_user.id)
    ).first()
    
    if not sched:
        raise HTTPException(status_code=400, detail="您在所选的日期没有值班安排，无法申请换班")

    # 2. 创建申请记录
    # 注意：target_date 可能有人值班（互换），也可能没人（单向移动），这里只记录意图
    request = SwapRequest(
        applicant_id=current_user.id,
        original_date=original_date,
        target_date=target_date,
        reason=reason,
        status=RequestStatus.PENDING
    )
    session.add(request)
    session.commit()
    return {"message": "换班申请已提交，等待管理员审核", "status": "success"}

@app.get("/swaps/pending")
def get_pending_swaps(
    session: SessionDep,
    admin: User = Depends(get_current_admin)
):
    """管理员获取所有待审核的申请"""
    # 关联查询出申请人的详细信息
    statement = select(SwapRequest, User).where(SwapRequest.applicant_id == User.id)\
                                         .where(SwapRequest.status == RequestStatus.PENDING)
    results = session.exec(statement).all()
    
    # 格式化返回
    data = []
    for req, user in results:
        data.append({
            "id": req.id,
            "applicant": user.real_name,
            "original_date": req.original_date,
            "target_date": req.target_date,
            "reason": req.reason,
            "created_at": req.created_at
        })
    return data

@app.post("/swaps/{request_id}/approve")
async def approve_swap(
    request_id: int,
    session: SessionDep,
    admin: User = Depends(get_current_admin)
):
    """
    管理员通过审核 -> 核心事务逻辑
    自动修改排班表：A和B互换，或者A移动到空位
    """
    # 1. 获取申请
    request = session.get(SwapRequest, request_id)
    if not request or request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="申请不存在或已处理")

    # 2. 获取当天的排班记录
    # 申请人原本的班
    schedule_src = session.exec(
        select(Schedule).where(Schedule.date == request.original_date)
    ).first()
    
    # 目标日期的班 (可能有人，也可能没人)
    schedule_dst = session.exec(
        select(Schedule).where(Schedule.date == request.target_date)
    ).first()

    if not schedule_src or schedule_src.user_id != request.applicant_id:
        request.status = RequestStatus.REJECTED
        session.add(request)
        session.commit()
        raise HTTPException(status_code=400, detail="排班表已变动，原定值班无效，自动驳回")

    # 3. 执行交换逻辑 (Atomic Transaction)
    # 情况A: 目标日期也有人值班 -> 互换人员
    if schedule_dst:
        # 记录一下是谁被换了
        target_user_id = schedule_dst.user_id
        # 互换
        schedule_dst.user_id = request.applicant_id
        schedule_src.user_id = target_user_id
        schedule_src.note = f"与 {request.target_date} 换班"
        schedule_dst.note = f"与 {request.original_date} 换班"
        
        session.add(schedule_dst)
    
    # 情况B: 目标日期是空的 -> 只有单向移动
    else:
        # 创建一个新班
        new_schedule = Schedule(
            date=request.target_date,
            user_id=request.applicant_id,
            status=ScheduleStatus.NORMAL,
            note="补班/调班"
        )
        session.add(new_schedule)
        # 删除旧班 (或者标记为已取消)
        session.delete(schedule_src)

    # 4. 更新申请状态
    session.add(schedule_src)
    request.status = RequestStatus.APPROVED
    session.add(request)
    
    session.commit()
    return {"message": "审批通过，排班表已自动更新", "status": "success"}

# --- 数据统计接口 ---

@app.get("/stats/me")
def get_my_stats(
    year: int,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的值班统计
    返回：年度总天数，每月分布
    """
    # 查询该用户全年的值班记录
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    schedules = session.exec(
        select(Schedule)
        .where(Schedule.user_id == current_user.id)
        .where(Schedule.date >= start_date)
        .where(Schedule.date <= end_date)
    ).all()
    
    total_days = len(schedules)
    
    # 按月统计
    monthly_stats = {m: 0 for m in range(1, 13)}
    for s in schedules:
        monthly_stats[s.date.month] += 1
        
    return {
        "year": year,
        "total_days": total_days,
        "monthly_breakdown": monthly_stats
    }


@app.get("/")
def read_root():
    return {"message": "AI值班系统后端已启动", "status": "running"}


@app.post("/test/notify")
async def manual_notify(
    admin: User = Depends(get_current_admin)
):
    """手动触发一次通知 (用于测试)"""
    await send_daily_reminder()
    return {"message": "通知已发送，请检查企业微信群", "status": "success"}
