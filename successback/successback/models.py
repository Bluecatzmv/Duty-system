from typing import Optional, List
import datetime  # 修改点1：改为导入整个模块，避免命名冲突
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

# 定义枚举类型，规范数据
class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

class ScheduleStatus(str, Enum):
    NORMAL = "normal"      # 正常值班
    SWAPPED = "swapped"    # 已换班出去

class RequestStatus(str, Enum):
    PENDING = "pending"    # 待审核
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝

# --- 数据库模型 (Tables) ---

class User(SQLModel, table=True):
    """员工表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    real_name: str
    department: Optional[str] = None
    phone: Optional[str] = None
    wechat_userid: Optional[str] = None
    password_hash: str
    role: Role = Field(default=Role.USER)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now) # 修改点2：使用 datetime.datetime

    # 关联关系
    # 注意：这里使用字符串 "Schedule" 是为了处理“前向引用”，因为 Schedule 类还没定义
    schedules: List["Schedule"] = Relationship(back_populates="user")
    requests: List["SwapRequest"] = Relationship(back_populates="applicant")

class Schedule(SQLModel, table=True):
    """值班日程表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 修改点3：字段名是 date，类型指定为 datetime.date，消除冲突
    date: datetime.date = Field(index=True)                 
    
    is_holiday: bool = Field(default=False)
    note: Optional[str] = None
    status: ScheduleStatus = Field(default=ScheduleStatus.NORMAL)
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    # 修改点4：为了稳健，关联对象的类型也加上引号 "User"
    user: Optional["User"] = Relationship(back_populates="schedules")

class SwapRequest(SQLModel, table=True):
    """换班申请表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    applicant_id: int = Field(foreign_key="user.id")
    
    # 修改点5：使用 datetime.date
    original_date: datetime.date
    target_date: datetime.date
    
    reason: Optional[str] = None
    status: RequestStatus = Field(default=RequestStatus.PENDING)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    applicant: Optional["User"] = Relationship(back_populates="requests")

class SystemSetting(SQLModel, table=True):
    """系统配置表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: str
    description: Optional[str] = None

# ... (保留上面的代码不变)

# --- 新增：用于API返回的安全模型 (不含密码) ---
class UserRead(SQLModel):
    id: int
    username: str
    real_name: str
    department: Optional[str] = None
    role: Role
    
    # 允许 API 自动从数据库模型转换过来
    class Config:
        from_attributes = True
