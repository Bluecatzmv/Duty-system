# 📅 可视化值班管理系统 (Duty System)

基于 FastAPI + Vue3 + Docker 的可视化值班管理系统。支持自动排班统计、企业微信通知、多维度数据分析及通讯录管理。
> **这是一个基于实际工作需求诞生，并通过“人机协作”模式开发的项目。**

## 💡 项目背景
在日常工作中，值班排班、通知发送以及调休统计往往占据了大量琐碎的时间。为了将重复劳动自动化、通知不及时的问题，开发了这套**值班系统**。

## 🤖 关于开发模式
本项目是一个典型的 **AI 辅助开发 (AI-Assisted Development)** 实践案例。
项目的大部分核心逻辑、前端界面以及 Docker 部署配置，均是在大型语言模型（LLM）的辅助下完成的。这种模式极大地提高了开发效率，也让非全职开发人员能够构建出功能完整的全栈应用。
   
## ✨ 主要功能

* **排班可视化**：基于 FullCalendar 的日历视图，支持按月度、年度展示。（目前可视化统计的信息目前仅识别技术值班人员，未能实现自定义）
* **自动化通知**：集成企业微信 Webhook，支持定时发送值班日报卡片。（对于通知内容数据获取的定义还在整理）
* **数据管理**：
    * 支持 Excel 批量导入/导出排班表和通讯录。
    * 提供“覆盖模式”与“追加模式”导入。
    * 值班信息卡片支持更换值班人员姓名后自动修改联系方式
* **智能统计**：
    * 自动计算值班分布（假期中间值班人员强化体现）。
    * 调休额度转换计算与兑换管理。（还没有接入自定义设置调休天数的界面）。
* **通讯录**：全员可查的通讯录，支持管理员在线编辑与维护。
* **权限系统**：分级权限（管理员/普通用户），对应不同的操作逻辑和显示许可。

## 🛠 主要界面展示
--**主页面**--
<img width="1920" height="962" alt="ee19263c32755644e82b1075bc0ebc1e" src="https://github.com/user-attachments/assets/ae3a4dc9-4db6-4ffb-bf0d-dfb1a9e88036" />
--**年度、月底值班信息总览**--
<img width="1920" height="962" alt="535e9967810916679839b20132220b1b" src="https://github.com/user-attachments/assets/49fe2ace-b281-480f-beaa-0f6d65016136" />
--**周番统计**--
<img width="1920" height="962" alt="49fdf11051d99983c9c8d0bc2661220b" src="https://github.com/user-attachments/assets/c6395fc0-c2c8-4625-9a3d-6f83d25ad412" />
--**节假日值班统计**--
<img width="1920" height="962" alt="280452da1de6d8b5f15d494b24bb0716" src="https://github.com/user-attachments/assets/ea123299-250e-45ec-a7b9-3c967e91bce1" />

## 🛠 技术栈

* **后端**：Python 3.12, FastAPI, SQLModel (SQLite), APScheduler
* **前端**：Vue 3, Naive UI, FullCalendar, Vite
* **部署**：Docker & Docker Compose

## 🚀 快速开始

### 1. 克隆项目

`git clone https://github.com/Bluecatzmv/Duty-system.git`


### 2. 启动服务
启动前在项目根目录下创建data目录，并进入目录创建`database.db`空文件：

* `mkdir data`
* `cd data`
* `touch database.db`

使用 Docker Compose 一键启动：

`docker-compose up -d --build`

* 前端访问：`http://localhost` (或服务器 IP)
* 后端文档：`http://localhost/api/docs`
* 配置ssl证书：frontend/nginx.conf（按需修改，已写好模版）
* 初始登陆信息：admin/admin123

## 📂 目录结构
* `/backend`: FastAPI 后端代码
* `/frontend`: Vue3 前端代码
* `/data`: 数据库持久化目录

## ⚠️ 声明与维护说明 (Disclaimer)
虽然本项目已在我的生产环境中稳定运行，但鉴于其开发模式及个人精力限制，请使用者注意以下几点：

1.  **代码维护**：由于核心代码由 AI 生成，部分逻辑可能存在冗余或非最佳实践。作为开发者，无法对所有底层代码细节做到 100% 的掌控。
2.  **Issue 响应**：这是一个个人开源项目，**维护和更新取决于我的业余时间**。对于复杂的 Bug 或新功能需求，我可能无法做到即时响应或修复。
3.  **安全性**：项目主要设计用于内网环境，未经过严格的渗透测试。请勿直接将其暴露在公网环境，建议配合 VPN 或内网穿透使用。
4.  **欢迎共建**：非常欢迎社区提交 Pull Request (PR) 来修复 Bug 或优化代码。如果你发现了逻辑错误，欢迎指正，我们将共同完善它。
