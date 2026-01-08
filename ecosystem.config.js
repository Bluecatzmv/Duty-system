module.exports = {
  apps: [
    {
      name: "frontend",
      script: "npm",
      args: "run dev",
      cwd: "./frontend", // 如果你的 package.json 在根目录，就写 ./
      watch: false
    },
    {
      name: "backend",
      // 这里指向虚拟环境里的 uvicorn
      script: "./venv/bin/uvicorn",
      // 这里的参数就是你手动运行时用的参数
      args: "main:app --reload --host 0.0.0.0 --port 8000",
      // 【关键点】告诉 PM2 不要用 nodejs 解释器，而是直接执行该脚本
      interpreter: "none",
      cwd: "./backend",
      watch: false
    }
  ]
};
