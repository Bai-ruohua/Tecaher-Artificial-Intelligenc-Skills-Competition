# Zeabur 部署指南

## 准备工作

1. **GitHub 账号** — 用于存放代码
2. **Zeabur 账号** — 打开 https://zeabur.com ，用 GitHub 登录即可

---

## 第 1 步：上传代码到 GitHub

### 方法 A：GitHub Desktop（推荐，最简单）

1. 下载安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录 GitHub 账号
3. 创建新仓库：`File → New repository`，名称 `ai-teaching-platform`
4. 打开项目文件夹 `C:\Users\Administrator\WorkBuddy\Tecaher-Artificial-Intelligenc-Skills-Competition\`
5. 把里面的全部文件拖进 GitHub Desktop 的窗口
6. 填摘要（如 `v4.7 部署`），点 `Commit to main`
7. 点 `Publish branch` → 代码就推到 GitHub 了

### 方法 B：命令行

```bash
# 打开项目目录
cd C:\Users\Administrator\WorkBuddy\Tecaher-Artificial-Intelligenc-Skills-Competition

# 初始化 Git（如果没有）
git init
git add .
git commit -m "v4.7 初始部署"

# 关联远程仓库（先到 GitHub 创建一个空仓库）
git remote add origin https://github.com/你的用户名/ai-teaching-platform.git
git push -u origin main
```

---

## 第 2 步：Zeabur 部署

1. 打开 https://zeabur.com ，用 GitHub 登录

2. 点 **「New Project」** → **「Deploy from GitHub」**

3. 授权 Zeabur 访问 GitHub → 选择刚才创建的 `ai-teaching-platform` 仓库

4. Zeabur 自动检测 Python 项目 → 自动安装依赖

5. **关键设置**（这一步一定要做）：
   - 在 Zeabur 项目页面 → **「Settings」** 或 **「Start Command」** 中，设置启动命令：
     ```
     gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2
     ```
   - 或者更简单：把启动命令改为：
     ```
     python run.py
     ```

6. **配置环境变量**：
   - Zeabur 项目 → **「Environment Variables」**
   - 添加变量：
     - `PORT` = `5000`
     - `DEEPSEEK_API_KEY` = `sk-你的key`（填你实际的 Key）
     - `PYTHONPATH` = `src`（重要！确保 Python 能找到 src 目录下的模块）

7. 等待部署完成（2-5 分钟），Zeabur 会自动生成一个 `xxxx.zeabur.app` 的访问地址

---

## 第 3 步：验证

拿到 Zeabur 给的链接后，在浏览器打开：
- `https://你的项目.zeabur.app/login` — 登录页
- 用 `admin / admin123` 登录

---

## 注意事项

### 数据库
- Zeabur 免费版**不支持持久化存储**，每次重启后数据库会重置为初始状态（只有 Python 课程和测试数据）
- 如果需要长期保存数据，后续可以升级到付费版开启持久化存储

### .env 文件
- Zeabur 上不需要 `.env` 文件，环境变量通过 Zeabur 控制台配置
- 如果本地测试，在项目目录下创建 `.env` 文件：
  ```
  DEEPSEEK_API_KEY=你的key
  ```

### 模板文件
- 项目依赖 `data/templates/` 下的 4 个 DOCX 模板文件
- 它们已经包含在项目中，会自动上传

---

## 遇到问题？

| 现象 | 原因 | 解决 |
|:----|:------|:------|
| 500 Internal Server Error | 可能缺少环境变量 | 检查 `PYTHONPATH=src` 是否设置 |
| ModuleNotFoundError | 依赖没装全 | 检查 requirements.txt 是否有 `gunicorn` |
| 登录后页面空白 | 数据库未初始化 | 第一次访问时耐心等待几秒 |
| 备课/AI 功能报错 | 未配置 API Key | 在 Zeabur 环境变量中添加 `DEEPSEEK_API_KEY` |
