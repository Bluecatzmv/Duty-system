# 📅 智能排班管理系统 (Duty Roster System)

基于 FastAPI + Vue3 + Docker 的现代化值班排班管理系统。支持自动排班统计、企业微信通知、多维度数据分析及通讯录管理。

## ✨ 主要功能

* **排班可视化**：基于 FullCalendar 的日历视图，支持按月展示。
* **自动化通知**：集成企业微信 Webhook，支持定时发送值班日报卡片。
* **数据管理**：
    * 支持 Excel 批量导入/导出排班表和通讯录。
    * 提供“覆盖模式”与“追加模式”导入。
* **智能统计**：
    * 自动计算值班分布（C位分析）。
    * 调休额度自动计算与兑换管理。
* **通讯录**：全员可查的通讯录，支持管理员在线编辑与维护。
* **权限系统**：JWT 认证，分级权限（管理员/普通用户/只读模式）。

## 🛠 技术栈

* **后端**：Python 3.12, FastAPI, SQLModel (SQLite), APScheduler
* **前端**：Vue 3, Naive UI, FullCalendar, Vite
* **部署**：Docker & Docker Compose

## 🚀 快速开始

### 1. 克隆项目
\`\`\`bash
git clone https://github.com/你的用户名/duty-roster.git
cd duty-roster
\`\`\`

### 2. 启动服务
使用 Docker Compose 一键启动：
\`\`\`bash
docker-compose up -d --build
\`\`\`

* 前端访问：`http://localhost` (或服务器 IP)
* 后端文档：`http://localhost/api/docs`

## 📂 目录结构
* `/backend`: FastAPI 后端代码
* `/frontend`: Vue3 前端代码
* `/data`: 数据库持久化目录
