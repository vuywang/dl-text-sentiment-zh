# 基于深度学习的中文文本情感分析系统

这是一个可以直接运行和答辩演示的中文文本情感分析系统。当前项目已经升级为“FastAPI + Vue3”的前后端协作方案，重点面向本科毕业设计答辩展示，支持 Vue3 可视化首页、单文本情感分析、CSV 批量分析报告、模型训练、模型评估增强、低置信度复核、误判样本分析、模型管理、历史记录查看和 SQLite 数据持久化。

当前仓库同时保留两套页面：

- Vue3 新版前端：适合毕业设计答辩展示，页面更美观，图表更完整。
- Jinja2 旧版页面：继续保留，作为后端原功能和兼容演示入口。

## 1. 快速启动

打开 Windows PowerShell，进入项目目录：

```powershell
cd D:\CodeProjects\dl-text-sentiment-zh
```

如果之前创建环境失败过，先删除旧环境：

```powershell
conda deactivate
conda env remove -n zh_sentiment_fastapi
```

创建 conda 环境：

```powershell
conda env create -f environment.yml
```

激活环境：

```powershell
conda activate zh_sentiment_fastapi
```

### 1.1 启动后端 FastAPI

```powershell
python run.py
```

看到下面内容说明服务已经启动：

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

后端地址：

```text
http://127.0.0.1:8000
```

也可以直接使用 uvicorn：

```powershell
uvicorn app.main:app --reload
```

### 1.2 启动前端 Vue3

新开一个 PowerShell 窗口，执行：

```powershell
cd D:\CodeProjects\dl-text-sentiment-zh\frontend
npm install
npm run dev
```

前端默认访问地址：

```text
http://127.0.0.1:5173
```

Vite 已配置代理：

- `/api` 代理到 FastAPI
- `/storage` 代理到 FastAPI

因此前端页面可以直接调用后端接口和读取混淆矩阵、损失曲线等图片文件。

项目当前已经兼容“仓库目录位置变化”的情况。即使数据库或 `metrics.json` 中保存的是旧电脑上的绝对路径，例如 `D:\CodeProjects\dl-text-sentiment-zh\storage\...`，只要把项目完整拷贝到另一台电脑，并保留 `storage/` 目录，系统也会自动映射到当前仓库下的 `storage/` 路径，不需要手工改 SQLite 里的旧路径。

### 1.3 日常启动方式

以后再次启动项目，建议开两个终端：

```powershell
# 终端 1：后端
cd D:\CodeProjects\dl-text-sentiment-zh
conda activate zh_sentiment_fastapi
python run.py
```

```powershell
# 终端 2：前端
cd D:\CodeProjects\dl-text-sentiment-zh\frontend
npm run dev
```

## 2. 新版页面怎么用

Vue3 新版页面默认访问：

```text
http://127.0.0.1:5173
```

主要页面与访问路径如下：

| 页面 | Vue 路径 | 展示重点 |
|---|---|---|
| 首页看板 | `/dashboard` | 统计卡片、情感占比饼图、最近趋势、模型指标雷达图、最近记录 |
| 单文本分析 | `/predict` | 文本输入、情感标签、积极/消极概率、置信度仪表盘、分析说明 |
| 批量分析 | `/batch` | CSV 上传、分析报告、置信度分布、文本长度分布、高频词、结果下载 |
| 模型训练 | `/train` | 训练参数表单、任务状态、训练记录、日志入口 |
| 模型评估 | `/evaluate` | Accuracy、Precision、Recall、F1、Loss 曲线、混淆矩阵、分类报告，兼容旧训练结果 |
| 低置信度复核 | `/review` | 低置信度文本、建议复核状态、来源类型、前端筛选 |
| 误判分析 | `/error-analysis` | 疑似难判样本、可能原因、正负概率、创建时间 |
| 模型管理 | `/models` | 模型列表、当前启用状态、启用操作、指标查看 |
| 历史记录 | `/history` | 单文本历史、批量任务历史、训练任务历史 |

批量分析演示推荐使用：

```text
storage/datasets/sample_batch.csv
```

CSV 要求：

- 必须包含 `text` 列
- 编码为 `utf-8` 或 `utf-8-sig`

批量分析导出文件保存到：

```text
storage/exports/
```

### 模型评估页说明

`/evaluate` 页面会优先展示前端统一风格的 ECharts 图表。

当前答辩版前端已经将 Loss 曲线固定为一组真实训练结果对应的 30 轮 `train_loss / val_loss` 序列，用于保证不同电脑、不同目录位置下的展示效果一致，不再依赖旧模型目录中的 `loss_curve.png` 图片是否存在。

Accuracy、Precision、Recall、F1、混淆矩阵、分类报告和模型信息仍然继续从后端接口读取。

### 保留的旧版页面

如果需要验证原有 Jinja2 页面仍可使用，可以继续访问：

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/predict
http://127.0.0.1:8000/batch
http://127.0.0.1:8000/train
http://127.0.0.1:8000/evaluate
http://127.0.0.1:8000/history
```

## 3. 答辩演示顺序

推荐直接使用 Vue3 新版前端按下面顺序演示：

1. 启动后端和前端，确认 `http://127.0.0.1:8000` 和 `http://127.0.0.1:5173` 可访问。
2. 打开 `/dashboard`，先介绍系统整体概况、当前启用模型、累计分析数量和图表看板。
3. 打开 `/predict`，输入一条积极文本和一条消极文本，展示情感标签、概率条、置信度仪表盘和分析说明。
4. 打开 `/batch`，上传 `storage/datasets/sample_batch.csv`，展示批量分析报告、饼图、柱状图和结果下载。
5. 打开 `/evaluate`，展示 Accuracy、Precision、Recall、F1-score、Loss 曲线、混淆矩阵和分类报告，并说明系统可兼容旧训练结果。
6. 打开 `/review`，展示低置信度文本需要人工复核的业务意义。
7. 打开 `/error-analysis`，说明中文情感分析中否定、转折和短文本问题对模型判断的影响。
8. 打开 `/models`，说明系统支持模型注册、启用和指标对比。
9. 打开 `/history`，展示 SQLite 持久化记录，包括单文本、批量任务和训练任务。
10. 如果老师想看训练入口，再打开 `/train` 介绍训练参数和日志入口，不建议现场跑长时间训练。

## 4. 常见问题

### 打开页面显示 Internal Server Error

先看运行窗口是否有报错，再看日志文件：

```text
storage/logs/app.log
```

修改代码后，`python run.py` 会自动重载。页面仍然报错时，按 `Ctrl + C` 停止服务，然后重新执行：

```powershell
python run.py
```

### 页面里的中文显示成问号

浏览器页面输入中文不会出现这个问题。使用 PowerShell 直接调用接口时，PowerShell 可能把中文请求体编码弄坏，导致数据库保存为问号。

系统已经增加中文输入校验，不包含中文字符的文本不会写入数据库。

### 第一次启动很慢

第一次启动会加载 `google-bert/bert-base-chinese` 模型，训练时会加载 ChnSentiCorp 数据集。下载和缓存需要时间。

模型缓存和数据缓存位置：

```text
storage/models/
storage/datasets/
```

### 训练很慢

BERT 模型训练需要较多计算资源。没有 GPU 时使用下面这组参数演示：

```text
epoch = 3
batch_size = 8
max_length = 64
```

需要展示更完整的损失曲线时，将 epoch 改成 30。

### 批量上传失败

检查 CSV 是否满足：

- 文件后缀是 `.csv`
- 编码使用 `utf-8-sig`，系统同时兼容 `utf-8`
- 表头包含 `text` 列

### 模型评估页仍显示旧图或 Loss 曲线没有更新

先确认后端和前端都已经重新启动：

```powershell
# 终端 1
cd D:\CodeProjects\dl-text-sentiment-zh
conda activate zh_sentiment_fastapi
python run.py
```

```powershell
# 终端 2
cd D:\CodeProjects\dl-text-sentiment-zh\frontend
npm run dev
```

然后在浏览器里对评估页执行强制刷新：

```text
Ctrl + F5
```

如果 `/evaluate` 页面中的混淆矩阵或模型信息没有更新，请检查下面几个文件是否存在：

```text
storage/models/archive/<model_dir>/metrics.json
```

## 5. 技术栈与版本

| 模块 | 技术与版本 |
|---|---|
| 环境管理 | conda，环境名 `zh_sentiment_fastapi` |
| Python | 3.14.3 |
| 后端 | FastAPI 0.135.3，Uvicorn 0.44.0 |
| 模板 | Jinja2 3.1.6 |
| 前端（新版） | Vue 3，Vite，Element Plus，Vue Router，Pinia，Axios，ECharts |
| 前端（旧版保留） | Jinja2 模板，Bootstrap 5.3.8，原生 JavaScript |
| 数据库 | SQLite，SQLAlchemy 2.0.49 |
| 文件上传 | python-multipart 0.0.26 |
| 深度学习 | PyTorch 2.11.0，Transformers 5.5.4 |
| 数据处理 | datasets 4.8.4，pandas 3.0.2，numpy 2.4.4，scikit-learn 1.8.0，matplotlib 3.10.8 |

固定模型：

```text
google-bert/bert-base-chinese
```

固定数据集：

```text
ChnSentiCorp
```

情感标签：

```text
0：消极
1：积极
```

## 6. 数据库说明

数据库文件位置：

```text
storage/db/app.db
```

应用首次启动会自动创建数据库表，不需要手动建表。

手动初始化数据库：

```powershell
python scripts/init_db.py
```

数据库中保存：

- 单文本分析记录
- 批量分析任务
- 训练任务
- 模型注册信息

## 7. SQLite 工具说明

用户本机 SQLite CLI 工具目录为：

```text
C:\soft\sqlite-tools-win-x64-3530000
```

该目录为本机 SQLite CLI 工具目录，可用于开发调试、查看表结构、导出数据。

可以使用该目录下的 `sqlite3.exe` 手动查看数据库：

```powershell
C:\soft\sqlite-tools-win-x64-3530000\sqlite3.exe storage\db\app.db
```

项目运行本身不依赖 `sqlite3.exe`。应用程序通过 Python、SQLAlchemy ORM 和 SQLite 数据库驱动完成数据库读写。

## 8. 目录说明

```text
project_root/
├─ app/                  后端应用代码
│  ├─ main.py            FastAPI 入口
│  ├─ core/              配置、数据库、日志
│  ├─ models/            ORM 表模型和请求模型
│  ├─ routers/           页面路由和 API 路由
│  ├─ services/          预测、批量、训练、历史记录服务
│  ├─ utils/             文件、文本、时间、图表工具
│  └─ templates/         Jinja2 页面模板
├─ frontend/             Vue3 前端工程（Vite + Element Plus + ECharts）
├─ static/               CSS、JavaScript、图片资源
├─ scripts/              训练、评估、数据库初始化脚本
├─ storage/              数据库、上传文件、导出文件、日志、模型、数据集
├─ environment.yml       conda 环境文件
├─ README.md             项目使用说明
└─ run.py                项目启动入口
```

## 9. API 接口

新版 Vue 前端通过 Axios 调用 API。主要接口如下：

```text
GET  /api/dashboard/summary
GET  /api/dashboard/charts
POST /api/predict
POST /api/batch/upload
GET  /api/batch/{task_id}
GET  /api/batch/{task_id}/download
POST /api/train/start
GET  /api/train/{task_id}
GET  /api/train/{task_id}/log
GET  /api/evaluate/latest
GET  /api/models
POST /api/models/{id}/activate
GET  /api/review/low-confidence
GET  /api/error-samples
GET  /api/history/analysis
GET  /api/history/batch
GET  /api/history/train
```

其中 `GET /api/evaluate/latest` 用于模型评估页，返回 Accuracy、Precision、Recall、F1、混淆矩阵、训练参数和模型信息。当前答辩版前端会固定展示一组真实训练结果对应的 Loss 曲线，以保证跨电脑演示时风格统一、展示稳定。

统一成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

统一失败响应：

```json
{
  "code": 1,
  "message": "错误信息",
  "data": null
}
```
