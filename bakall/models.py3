from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from typing import Optional, List
import datetime 

# --- 1. 定义岗位类型 ---
class DutyType(str, Enum):
    LEADER = "总值班"
    TECH = "技术值班"
    DAY = "日间值班"
    NIGHT = "夜间值班"
    NIGHT_TRAINEE = "夜间见习"
    UPDATE = "更新值班"
    TRAINEE = "更新见习"
    BUSINESS = "业务值班" 

# --- 2. 角色定义 ---
class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"

# --- 3. 用户表 ---
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    real_name: str 
    password_hash: str
    role: Role = Field(default=Role.ADMIN)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

class UserRead(SQLModel):
    id: int
    username: str
    real_name: str
    role: Role

class UserCreate(SQLModel):
    username: str
    real_name: str
    password: str
    role: Role = Role.ADMIN

# --- 4. 人员信息表 ---
class Staff(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    real_name: str = Field(index=True, unique=True)
    department: Optional[str] = None
    phone: Optional[str] = None
    schedules: List["Schedule"] = Relationship(back_populates="staff")

# --- 5. 节假日表 (已修改：支持叠加保障期) ---
class HolidayType(str, Enum):
    HOLIDAY = "holiday"   # 休 (法定节假日)
    WORKDAY = "workday"   # 班 (调休补班)
    # 移除 GUARANTEE，它不再是互斥类型，改为下方的 bool 字段

class Holiday(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime.date = Field(index=True, unique=True)
    
    # 休/班 相关
    name: Optional[str] = None        # 例如：春节、中秋节
    type: Optional[HolidayType] = None # 允许为空（即普通周末或工作日，但可能是保障期）

    # 保障期叠加属性
    is_guarantee: bool = Field(default=False) # 是否为重要保障期
    guarantee_name: Optional[str] = None      # 例如：两会保障、防汛保障

# --- 6. 调休明细表 ---
class Redemption(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    schedule_id: int = Field(foreign_key="schedule.id")
    redeem_date: datetime.date
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    schedule: Optional["Schedule"] = Relationship(back_populates="redemptions")

# --- 7. 排班表 ---
class Schedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime.date = Field(index=True)
    staff_id: Optional[int] = Field(foreign_key="staff.id", default=None)
    staff: Optional[Staff] = Relationship(back_populates="schedules")
    staff_name: str 
    duty_type: DutyType
    redeemed_count: int = Field(default=0)
    redemptions: List[Redemption] = Relationship(back_populates="schedule")

class ScheduleRead(SQLModel):
    id: int
    date: datetime.date
    duty_type: DutyType
    staff_name: str
    staff_phone: Optional[str] = None
    redeemed_count: int = 0

# --- 8. 系统配置表 ---
class SystemConfig(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str

# --- 9. 导入文件表 ---
class ImportLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    import_type: str  # "schedule" 或 "contact"
    operator_name: str
    import_time: datetime.datetime = Field(default_factory=datetime.datetime.now)
    description: Optional[str] = None # 例如 "2026年1月排班"
    row_count: int = 0
