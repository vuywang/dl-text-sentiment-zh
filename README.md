# 基于深度学习的中文文本情感分析系统

这是一个可以直接运行和答辩演示的中文文本情感分析系统。系统支持单文本分析、CSV 批量分析、模型训练、模型评估、历史记录查看和 SQLite 数据持久化。

系统启动后在浏览器中使用，不需要打开 notebook，不需要启动前端工程，不需要安装 Node.js。

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

启动项目：

```powershell
python run.py
```

看到下面内容说明服务已经启动：

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

浏览器打开：

```text
http://127.0.0.1:8000
```

以后再次启动项目，只需要执行：

```powershell
cd D:\CodeProjects\dl-text-sentiment-zh
conda activate zh_sentiment_fastapi
python run.py
```

项目也可以直接用 uvicorn 启动：

```powershell
uvicorn app.main:app --reload
```

## 2. 页面怎么用

### 首页

访问：

```text
http://127.0.0.1:8000/
```

首页用于总览系统状态，可以看到：

- 当前激活模型
- 数据库连接状态
- 已分析文本总数
- 积极和消极文本数量
- 最近训练记录
- 最近分析记录
- 情感类别统计图

答辩演示时先打开首页，让老师看到这是一个完整系统，不是单独脚本。

### 单文本分析

访问：

```text
http://127.0.0.1:8000/predict
```

使用方法：

1. 在文本框输入一段中文文本。
2. 点击“开始分析”。
3. 页面显示预测结果。

返回内容包括：

- 情感标签：积极或消极
- 置信度
- 积极概率
- 消极概率
- 使用的模型名称

页面下方会显示最近 10 条分析记录。

可以测试这些文本：

```text
这家酒店服务很好，房间干净整洁。
物流太慢了，包装也有破损。
这部电影剧情紧凑，演员表现很自然。
客服态度不好，问题一直没有解决。
商品质量不错，价格也合适。
```

### 批量分析

访问：

```text
http://127.0.0.1:8000/batch
```

使用方法：

1. 准备一个 CSV 文件。
2. CSV 文件必须包含一列 `text`。
3. 点击上传并分析。
4. 页面显示本次任务统计、积极/消极占比图和结果预览。
5. 点击“下载结果 CSV”导出分析结果。

示例 CSV 已经放在：

```text
storage/datasets/sample_batch.csv
```

CSV 格式示例：

```csv
text
这家酒店服务很好，房间干净整洁。
物流太慢了，包装也有破损。
商品质量不错，价格也合适。
```

导出的结果文件会保存到：

```text
storage/exports/
```

导出 CSV 包含：

- text
- predicted_label
- confidence
- positive_score
- negative_score

命令行脚本批量分析：

```powershell
python scripts/batch_predict.py --input storage/datasets/sample_batch.csv
```

指定输出文件：

```powershell
python scripts/batch_predict.py --input storage/datasets/sample_batch.csv --output storage/exports/my_batch_result.csv
```

只导出 CSV，不写入单文本分析历史：

```powershell
python scripts/batch_predict.py --input storage/datasets/sample_batch.csv --no-history
```

脚本运行完成后会输出任务 ID、输入文件、输出文件、文本总数、积极数量和消极数量。脚本会把批量任务写入 `batch_task` 表，默认也会把每一条预测结果写入 `analysis_record` 表。

### 模型训练

访问：

```text
http://127.0.0.1:8000/train
```

页面可以设置训练参数：

- epoch
- batch_size
- learning_rate
- max_length

点击“开始训练”后，系统会创建训练任务，任务状态写入数据库。训练完成后，系统会保存：

- 模型权重
- tokenizer
- 训练配置
- 评估指标
- 混淆矩阵图片
- 损失曲线图片

模型保存目录：

```text
storage/models/archive/
```

训练日志目录：

```text
storage/logs/
```

当前项目已经提前训练过一版 30 epoch 演示模型，打开“模型评估”页面可以直接看到指标和损失曲线。

### 模型评估

访问：

```text
http://127.0.0.1:8000/evaluate
```

该页面展示当前已完成训练任务的评估结果，包括：

- Accuracy
- Precision
- Recall
- F1-score
- 混淆矩阵图
- 训练损失曲线
- 测试样例预测结果

如果损失曲线只有一个点，说明当前模型只训练了 1 个 epoch。训练多个 epoch 后，曲线会显示为连续折线。

### 历史记录

访问：

```text
http://127.0.0.1:8000/history
```

历史记录页面可以查看：

- 单文本分析历史
- 批量分析任务历史
- 模型训练任务历史

记录按时间倒序展示，数据来自 SQLite 数据库。

## 3. 答辩演示顺序

答辩时按这个顺序演示最清楚：

1. 打开首页，说明系统名称、当前激活模型、数据库状态和统计图。
2. 打开单文本分析页，输入一条积极文本和一条消极文本，展示预测结果。
3. 打开批量分析页，上传 `storage/datasets/sample_batch.csv`，展示统计图和结果导出。
4. 打开模型训练页，说明训练参数和训练记录。
5. 打开模型评估页，展示 Accuracy、Precision、Recall、F1-score、混淆矩阵和损失曲线。
6. 打开历史记录页，展示分析记录、批量任务记录和训练任务记录。

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

## 5. 技术栈与版本

| 模块 | 技术与版本 |
|---|---|
| 环境管理 | conda，环境名 `zh_sentiment_fastapi` |
| Python | 3.14.3 |
| 后端 | FastAPI 0.135.3，Uvicorn 0.44.0 |
| 模板 | Jinja2 3.1.6 |
| 前端 | Bootstrap 5.3.8，Apache ECharts 6.0.0，原生 JavaScript |
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
├─ static/               CSS、JavaScript、图片资源
├─ scripts/              训练、评估、数据库初始化脚本
├─ storage/              数据库、上传文件、导出文件、日志、模型、数据集
├─ environment.yml       conda 环境文件
├─ README.md             项目使用说明
└─ run.py                项目启动入口
```

## 9. API 接口

页面通过原生 JavaScript 调用 API。主要接口如下：

```text
POST /api/predict
POST /api/batch/upload
GET  /api/batch/{task_id}
GET  /api/batch/{task_id}/download
POST /api/train/start
GET  /api/train/{task_id}
GET  /api/history/analysis
GET  /api/history/batch
GET  /api/history/train
```

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
