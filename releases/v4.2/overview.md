# AI 智能教学平台 V4.0 交付概览

> 宜宾工业职业技术学院 · 数字经济学院 · 四川省第二届教师人工智能应用能力大赛（赛道三）
> 平台版本：**4.0**
> 版本规范：大更新→V5/V6，小更新→v4.x

## 当前版本核心成果

V4.0 在 V3.0（课程无关化 + 师生共用智能体 + 双端首页功能区）基础上，进行了体验升级与文档规范化。

### 1. 学情分析全面重构（核心亮点）
- 从纯文本 JSON 输入框升级为 **ECharts 5.5 多维度可视化看板**
- 雷达图（按课程 module 动态聚合）、章节掌握度柱状图（颜色5级）、综合分分布甜甜圈图、学习活跃度散点图、学生排名表（金银铜牌）
- AI 智能分析支持 `use_db: true` 一键从数据库取成绩分析
- 新增 `GET /api/analytics/db-grades` 接口直连数据库

### 2. 首页 9 卡 3×3 布局
- 严格 `repeat(3, 1fr)` 三列网格
- 每张卡独立色系（靛蓝/天蓝/紫色/翠绿/琥珀/红色/青色/深靛蓝/玫红）
- 右上角数据角标 + hover 顶部色条亮起 + 卡片上浮动效
- 响应式：≤768px 2 列，≤520px 1 列

### 3. 9 大模块测试数据一键生成
- 10 名学生 / 15 道题 / 8 份成绩 / 29 条答题 / 8 条 QA / 3 份教案 / 3 个数字人缓存

### 4. 项目结构规范化
- **代码与模板分离**：所有 Python 源码移入 `src/` 目录，`templates/`（HTML）、`static/`（CSS/JS）独立在根目录
- 根目录清爽：仅 `run.py` + 文档 + 配置文件
- `src/modules/`：9 个业务模块（备课/命题/批改/学情/智能体/知识库/图谱/数字人/数据同步）
- `src/scripts/`：测试数据生成、回归测试、快照脚本
- 版本管理规范化：明确"大更新 V5/V6，小更新 v4.x"规则

## 项目结构

```
项目根目录/
│
├── run.py                     # 启动入口
├── requirements.txt           # 依赖清单
├── .env                       # AI 密钥配置
├── .gitignore                 # Git 忽略规则
├── CHANGELOG.md               # 版本变更日志
├── overview.md                # 当前版本概览
│
├── src/                       # Python 源码
│   ├── app.py                 # Flask 主应用
│   ├── config.py              # 全局配置
│   ├── database.py            # 数据库模型
│   ├── knowledge_base.py      # 章节/模块数据
│   ├── rag_engine.py          # RAG 引擎
│   ├── auth.py                # 认证鉴权
│   ├── deepseek_client.py     # AI API 封装
│   └── modules/               # 9个业务模块
│
├── scripts/                   # 独立工具脚本
│   ├── check.py               # 导入/种子验证
│   ├── regress.py             # 回归测试
│   ├── seed_test_data.py      # 测试数据生成
│   └── snapshot.py            # 版本快照
│
├── templates/                 # HTML 模板
│   ├── login.html / base.html
│   ├── teacher/ (6 pages)
│   └── student/ (5 pages)
│
├── static/css/               # 样式文件
│
├── data/                     # 运行时数据
│   ├── db/                    # SQLite 数据库
│   ├── knowledge/             # 知识库文档
│   ├── vectors/               # 向量索引
│   ├── chroma_db/             # Chroma 持久化
│   └── digital_human_cache/   # 数字人缓存
│
├── docs/                     # 项目文档
│   ├── 项目实施梳理报告.md     # 完整项目梳理
│   └── versions/              # 版本升级方案
│
└── releases/                 # 可回滚代码快照
    ├── v2.1/ (44 files)
    ├── v3.0/ (48 files)
    └── v4.0/ (51 files)
```

## 关键文件

| 文件 | 作用 |
|------|------|
| `src/app.py` | Flask 主应用（双端路由 + 课程上下文） |
| `src/database.py` | 课程租户数据模型（含 grades 加 course_id） |
| `src/auth.py` | 登录认证 + 角色鉴权 + 课程上下文 |
| `src/modules/student_agents.py` | 4 大智能体核心（师生共用） |
| `src/modules/knowledge_store.py` | 文档入库/切片/检索 |
| `src/modules/data_sync.py` | 雷达/排名/甘特数据同步 |
| `templates/teacher/analytics.html` | 学情看板（ECharts 可视化） |
| `templates/teacher/dashboard.html` | 教师首页（3×3 布局） |
| `scripts/seed_test_data.py` | 测试数据生成脚本 |

## 版本闸门（V4.0）

- ✅ `CHANGELOG.md` — 已更新 [4.0] 条目
- ✅ `docs/versions/V4升级梳理计划.md` — 已创建
- ✅ `releases/v4.0/` — 已创建（51 文件）
- ✅ `config.PLATFORM_VERSION = "4.0"` — 已更新

## 验证状态

- HTTP 冒烟：✅ 10+ API 接口全部正常
- 回归测试：✅ V3 14/14 继承通过
- 数据库：✅ grades 表新增 course_id，迁移兼容

## 运行方式

```bash
cd Tecaher-Artificial-Intelligenc-Skills-Competition

# Python 源码在 src/ 目录，通过 run.py 启动
python run.py
# 或直接指定模块：python -m src.app

# 访问 http://127.0.0.1:5000（默认端口 5000）
# 默认教师账号：admin / admin123
```

## 后续 / 待办

- 🔴 P0: 配置 DEEPSEEK_API_KEY
- 🔴 P0: 了解学习通上传要求
- 🟡 P1: 部署到 CloudStudio 公网
- 🟡 P1: 采集真实使用数据
- 🟢 P2: 甘特图真实时间轴
