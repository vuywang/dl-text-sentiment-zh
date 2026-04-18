# AGENTS.md

本文件是给后续代理和协作者看的项目协作说明，适用于整个仓库。

## 项目简介

这是一个基于深度学习的中文文本情感分析系统。项目使用 FastAPI 提供页面和 API，使用 Jinja2 渲染页面，使用 SQLite + SQLAlchemy 保存分析记录、批量任务、训练任务和模型注册信息，使用 PyTorch + Transformers 加载 `google-bert/bert-base-chinese` 完成中文情感二分类。

核心功能包括：

- 单文本情感分析：输入中文文本，输出积极/消极、置信度和正负向概率。
- CSV 批量分析：上传包含 `text` 列的 CSV，生成批量预测结果和统计图。
- 历史记录管理：单文本和批量分析记录分来源保存，支持查看批量明细、下载结果和删除数据库记录。
- 模型训练：基于 ChnSentiCorp 数据集微调 BERT，并保存模型、指标和图表。
- 模型评估：展示 Accuracy、Precision、Recall、F1、混淆矩阵和损失曲线。
- 历史记录：将预测、批量任务和训练任务持久化到 SQLite。

## 常用命令

在 Windows PowerShell 中进入项目根目录：

```powershell
cd D:\CodeProjects\dl-text-sentiment-zh
```

创建和激活环境：

```powershell
conda env create -f environment.yml
conda activate zh_sentiment_fastapi
```

启动 Web 服务：

```powershell
python run.py
```

也可以直接使用 Uvicorn：

```powershell
uvicorn app.main:app --reload
```

初始化数据库和默认模型记录：

```powershell
python scripts/init_db.py
```

命令行批量分析：

```powershell
python scripts/batch_predict.py --input storage/datasets/sample_batch.csv
```

评估当前激活模型：

```powershell
python scripts/evaluate_model.py
```

## 目录职责

- `run.py`：本地启动入口，负责启动 `app.main:app`。
- `app/main.py`：FastAPI 应用入口，挂载静态资源、注册路由、初始化目录、数据库和模型。
- `app/core/`：项目配置、数据库连接和日志工具。
- `app/models/db/`：SQLAlchemy ORM 表模型。
- `app/models/schema/`：请求参数和接口数据校验模型。
- `app/routers/`：页面路由和 API 路由。
- `app/services/`：业务逻辑层，包含预测、批量处理、训练、历史记录和模型管理。
- `app/templates/`：Jinja2 页面模板。
- `app/utils/`：文件、文本、响应、时间和图表工具。
- `static/`：页面 CSS 和 JavaScript。
- `scripts/`：初始化数据库、批量预测、训练和评估脚本。
- `storage/`：运行期数据，包括数据库、上传文件、导出文件、日志、数据集缓存和模型文件。

## 编码与文档规范

- 中文 Markdown、Python 字符串和模板文件统一使用 UTF-8。
- 在 PowerShell 中查看中文文件时优先使用：

```powershell
Get-Content -Encoding UTF8 -Path README.md
```

- Markdown 中的命令要使用 fenced code block，并标注 `powershell`、`text`、`json` 等语言。
- 项目说明面向答辩和运行演示，文字应直接说明“怎么启动、怎么演示、结果在哪里看”。

## 代码修改原则

- 路由层保持轻量：参数接收、依赖注入和响应封装放在 `app/routers/`，业务细节放到 `app/services/`。
- 新增页面功能时，通常需要同时检查 `router`、`service`、`schema`、`template`、`static/js` 是否需要更新。
- 新增数据库字段时，先更新 `app/models/db/` 中的 ORM 模型，再确认初始化和页面读取逻辑是否一致。
- API 成功响应尽量使用 `app.utils.response.success`，失败响应使用 `fail`，保持 `code/message/data` 结构统一。
- 文本输入、CSV 上传和路径处理要复用 `app/utils/` 中已有工具，避免在路由里重复写校验逻辑。
- 涉及训练、预测、模型加载的逻辑要注意 CPU/GPU 兼容，默认不能假设一定有 CUDA。

## 数据、模型和运行产物

- 不要随意修改或删除 `storage/` 下的运行产物，尤其是：
  - `storage/db/app.db`
  - `storage/models/current/`
  - `storage/models/archive/`
  - `storage/datasets/`
  - `storage/logs/`
  - `storage/exports/`
- 如需新增演示数据，优先使用 `storage/datasets/sample_batch.csv` 的格式：首列标题为 `text`，内容为中文文本。
- 批量分析导出的 CSV 建议放在 `storage/exports/`。
- 训练得到的新模型应由训练流程登记到 `model_registry`，不要手动硬改当前激活模型状态，除非任务明确要求。
- 历史页的“清空”和“删除选中”会删除 SQLite 数据库中的记录。当前实现只删除数据库记录，不主动删除 `storage/exports/` 下已经导出的 CSV 文件。

## 历史记录与删除规则

`analysis_record` 使用 `source_type` 区分记录来源：

- `single`：单文本分析产生的记录，`batch_task_id` 为空。
- `batch`：批量分析产生的明细记录，`batch_task_id` 指向对应的 `batch_task.id`。

删除规则：

- 删除选中的单文本记录：只删除 `source_type = single` 且 ID 被选中的 `analysis_record`。
- 清空单文本记录：删除全部 `source_type = single` 的 `analysis_record`。
- 删除选中的批量任务：删除选中的 `batch_task`，并删除 `source_type = batch` 且 `batch_task_id` 属于这些任务的明细。
- 清空批量任务：删除全部 `batch_task`，并删除全部 `source_type = batch` 的明细。
- 训练任务记录暂不提供清空入口，避免误删训练评估信息。

旧数据库会在 `init_db()` 时自动补充 `source_type` 和 `batch_task_id` 字段。旧的分析记录默认标记为 `single`，因为旧数据没有可靠字段判断它是否来自批量任务。

## 训练与预测流程约定

单文本预测主线：

```text
用户输入中文文本 -> 文本校验 -> 当前激活模型加载 -> tokenizer 编码 -> BERT 推理 -> softmax 概率 -> 保存 analysis_record
```

批量预测主线：

```text
上传 CSV -> 保存上传文件 -> 创建 batch_task -> 检查 text 列 -> 逐行文本校验 -> 逐行预测 -> 保存批量明细 -> 保存结果 CSV -> 更新 batch_task
```

训练任务主线：

```text
页面提交训练参数 -> 创建 train_task -> 后台启动 scripts/train_model.py -> 加载 ChnSentiCorp -> 训练与验证 -> 保存模型和指标 -> 注册新模型为 active
```

答辩或日常验证时不要默认现场跑长时间训练。需要演示训练入口时，可以使用较小参数，例如 `epoch=1`、`batch_size=8`、`max_length=64`，并重点展示已有训练结果和评估页面。

## 手工验证清单

当前仓库没有现成的自动化测试文件。修改代码后，至少按改动范围选择下面的验证方式：

```powershell
python -m compileall app scripts
```

```powershell
python scripts/init_db.py
```

```powershell
python scripts/batch_predict.py --input storage/datasets/sample_batch.csv --output storage/exports/agent_check.csv --no-history
```

```powershell
python scripts/evaluate_model.py
```

```powershell
python run.py
```

页面功能建议手工检查：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/predict`
- `http://127.0.0.1:8000/batch`
- `http://127.0.0.1:8000/train`
- `http://127.0.0.1:8000/evaluate`
- `http://127.0.0.1:8000/history`

## 答辩演示提醒

答辩时按业务闭环讲最清楚：

1. 首页展示系统状态、当前激活模型和数据库状态。
2. 单文本预测展示即时推理能力。
3. 批量分析上传 `storage/datasets/sample_batch.csv`，展示统计和导出文件。
4. 训练页说明训练参数和后台任务，不建议现场跑长训练。
5. 评估页展示 Accuracy、Precision、Recall、F1、混淆矩阵和损失曲线。
6. 历史记录页展示 SQLite 持久化结果。
