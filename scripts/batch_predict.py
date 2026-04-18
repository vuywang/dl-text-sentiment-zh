import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, init_db  # noqa: E402
from app.models.db.analysis_record import AnalysisRecord  # noqa: E402
from app.models.db.batch_task import BatchTask  # noqa: E402
from app.services.model_service import ensure_default_model, predict_text  # noqa: E402
from app.utils.file_utils import ensure_text_column, read_csv_compatible  # noqa: E402
from app.utils.text_utils import require_text  # noqa: E402
from app.utils.time_utils import now_str  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="命令行批量中文情感分析脚本")
    parser.add_argument(
        "--input",
        required=True,
        help="输入 CSV 文件路径，必须包含 text 列",
    )
    parser.add_argument(
        "--output",
        default="",
        help="输出 CSV 文件路径，不填写时自动保存到 storage/exports/",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=settings.DEFAULT_MAX_LENGTH,
        help="BERT tokenizer 最大长度",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="只导出 CSV，不写入 analysis_record 历史记录",
    )
    return parser.parse_args()


def resolve_input_path(raw_path: str) -> Path:
    input_path = Path(raw_path)
    if not input_path.is_absolute():
        input_path = settings.ROOT_DIR / input_path
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{input_path}")
    if input_path.suffix.lower() != ".csv":
        raise ValueError("输入文件必须是 CSV 格式")
    return input_path


def resolve_output_path(raw_path: str, task_id: int) -> Path:
    if raw_path:
        output_path = Path(raw_path)
        if not output_path.is_absolute():
            output_path = settings.ROOT_DIR / output_path
        if output_path.suffix.lower() != ".csv":
            raise ValueError("输出文件必须是 CSV 格式")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    output_path = settings.EXPORT_DIR / f"script_batch_result_{task_id}_{now_str()}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def save_analysis_record(db, text: str, result: dict[str, float | str], batch_task_id: int) -> None:
    db.add(
        AnalysisRecord(
            input_text=text,
            predicted_label=str(result["predicted_label"]),
            confidence=float(result["confidence"]),
            positive_score=float(result["positive_score"]),
            negative_score=float(result["negative_score"]),
            model_name=str(result["model_name"]),
            source_type="batch",
            batch_task_id=batch_task_id,
        )
    )


def run_batch_predict(args: argparse.Namespace) -> dict[str, object]:
    input_path = resolve_input_path(args.input)
    init_db()

    db = SessionLocal()
    task: BatchTask | None = None
    try:
        ensure_default_model(db)
        task = BatchTask(
            original_file_name=input_path.name,
            saved_file_path=str(input_path),
            total_count=0,
            positive_count=0,
            negative_count=0,
            result_file_path=None,
            status="running",
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        df = read_csv_compatible(input_path)
        ensure_text_column(df)

        rows: list[dict[str, object]] = []
        positive_count = 0
        negative_count = 0

        for row_index, value in enumerate(df["text"].tolist(), start=2):
            if pd.isna(value):
                raise ValueError(f"第 {row_index} 行 text 不能为空")
            text = require_text(str(value))
            result = predict_text(text, db, max_length=args.max_length)
            if result["predicted_label"] == "积极":
                positive_count += 1
            else:
                negative_count += 1

            if not args.no_history:
                save_analysis_record(db, text, result, task.id)

            rows.append(
                {
                    "text": text,
                    "predicted_label": result["predicted_label"],
                    "confidence": result["confidence"],
                    "positive_score": result["positive_score"],
                    "negative_score": result["negative_score"],
                }
            )

        output_path = resolve_output_path(args.output, task.id)
        pd.DataFrame(rows).to_csv(output_path, index=False, encoding="utf-8-sig")

        task.total_count = len(rows)
        task.positive_count = positive_count
        task.negative_count = negative_count
        task.result_file_path = str(output_path)
        task.status = "completed"
        db.commit()

        return {
            "task_id": task.id,
            "input_path": str(input_path),
            "output_path": str(output_path),
            "total_count": len(rows),
            "positive_count": positive_count,
            "negative_count": negative_count,
        }
    except Exception:
        if task is not None:
            task.status = "failed"
            db.commit()
        raise
    finally:
        db.close()


def main() -> None:
    args = parse_args()
    result = run_batch_predict(args)
    print("批量分析完成")
    print(f"任务 ID：{result['task_id']}")
    print(f"输入文件：{result['input_path']}")
    print(f"输出文件：{result['output_path']}")
    print(f"文本总数：{result['total_count']}")
    print(f"积极数量：{result['positive_count']}")
    print(f"消极数量：{result['negative_count']}")


if __name__ == "__main__":
    main()
