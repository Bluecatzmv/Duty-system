i因为你已经配置好了 `ecosystem.config.js`，管理起来非常简单。你只需要在项目根目录（即 `ecosystem.config.js` 所在的目录）执行以下命令：

### 1. 运行服务 (Run/Start)

如果服务还没启动，或者你之前执行了 `delete` 命令删除了进程，用这个命令一键启动：

```bash
pm2 start ecosystem.config.js

```

*(如果进程已经在列表中只是被停止了，也可以用 `pm2 start all`)*

### 2. 重启服务 (Restart)

当你修改了代码（比如改了 `backend/main.py` 或前端代码），或者服务出现异常时，用这个命令重启：

```bash
# 重启所有服务（前端+后端）
pm2 restart all

# 如果只想重启后端
pm2 restart backend

```

### 3. 停止服务 (Stop)

如果你想暂时关掉服务，但保留在 PM2 的列表中：

```bash
pm2 stop all

```

### 4. 彻底删除服务 (Delete)

如果你想彻底关闭服务并从 PM2 列表中移除（下次启动需要重新 `pm2 start ecosystem.config.js`）：

```bash
pm2 delete all

```

### 💡 两个极其常用的辅助命令

* **查看运行状态**（看服务是 Online 还是 Error）：
```bash
pm2 list

```


* **查看实时日志**（排查报错必用）：
```bash
pm2 logs
# 或者只看后端的日志
pm2 logs backend

```
