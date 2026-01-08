# --- 第一阶段：构建 (Build) ---
FROM node:22 as build-stage

WORKDIR /app

# 复制 package.json 并安装依赖
COPY package*.json ./
# 如果在国内服务器构建，可以取消下面这行的注释使用淘宝源
# RUN npm config set registry https://registry.npmmirror.com
RUN npm install

# 复制源代码并打包
COPY . .
RUN npm run build

# --- 第二阶段：运行 (Run) ---
FROM nginx:stable-alpine as production-stage

# 从第一阶段复制打包好的 dist 目录到 Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制我们在上一步写的 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
