import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch
from datasets import load_dataset
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, init_db  # noqa: E402
from app.models.db.model_registry import ModelRegistry  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="评估当前激活中文情感模型")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=128)
    return parser.parse_args()


def collate_batch(batch: list[dict[str, object]], tokenizer, max_length: int) -> dict[str, torch.Tensor]:
    texts = [str(item["text"]) for item in batch]
    labels = torch.tensor([int(item["label"]) for item in batch], dtype=torch.long)
    encoded = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=max_length,
        return_tensors="pt",
    )
    encoded["labels"] = labels
    return encoded


def plot_confusion_matrix(matrix: np.ndarray, output_path: Path) -> None:
    plt.figure(figsize=(5, 4))
    plt.imshow(matrix, interpolation="nearest", cmap="Blues")
    plt.title("混淆矩阵")
    plt.colorbar()
    labels = ["消极", "积极"]
    tick_marks = np.arange(len(labels))
    plt.xticks(tick_marks, labels)
    plt.yticks(tick_marks, labels)
    threshold = matrix.max() / 2 if matrix.max() > 0 else 0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            plt.text(
                j,
                i,
                format(matrix[i, j], "d"),
                horizontalalignment="center",
                color="white" if matrix[i, j] > threshold else "black",
            )
    plt.ylabel("真实标签")
    plt.xlabel("预测标签")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def main() -> None:
    args = parse_args()
    init_db()
    db = SessionLocal()
    try:
        active = db.query(ModelRegistry).filter(ModelRegistry.is_active.is_(True)).first()
        if active is None:
            raise RuntimeError("当前没有激活模型")
        model_dir = Path(active.model_dir)
        model_source = str(model_dir) if (model_dir / "config.json").exists() else settings.PRETRAINED_MODEL_NAME
    finally:
        db.close()

    dataset = load_dataset(settings.DATASET_HF_ID, cache_dir=str(settings.DATASET_DIR))
    eval_split = "test" if "test" in dataset else "validation"
    eval_dataset = dataset[eval_split]

    tokenizer = AutoTokenizer.from_pretrained(model_source)
    model = AutoModelForSequenceClassification.from_pretrained(model_source, num_labels=2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    loader = DataLoader(
        eval_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        collate_fn=lambda batch: collate_batch(batch, tokenizer, args.max_length),
    )

    total_loss = 0.0
    total_batches = 0
    preds: list[int] = []
    labels: list[int] = []
    with torch.no_grad():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            total_loss += float(outputs.loss.item())
            total_batches += 1
            preds.extend(torch.argmax(outputs.logits, dim=-1).cpu().tolist())
            labels.extend(batch["labels"].cpu().tolist())

    matrix = confusion_matrix(labels, preds, labels=[0, 1])
    metrics = {
        "model_source": model_source,
        "dataset": settings.DATASET_NAME,
        "eval_loss": total_loss / max(total_batches, 1),
        "accuracy": float(accuracy_score(labels, preds)),
        "precision_score": float(precision_score(labels, preds, zero_division=0)),
        "recall_score": float(recall_score(labels, preds, zero_division=0)),
        "f1_score": float(f1_score(labels, preds, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
    }

    metrics_path = settings.LOG_DIR / "evaluate_metrics.json"
    matrix_path = settings.LOG_DIR / "evaluate_confusion_matrix.png"
    with metrics_path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)
    plot_confusion_matrix(matrix, matrix_path)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"评估指标文件：{metrics_path}")
    print(f"混淆矩阵图片：{matrix_path}")


if __name__ == "__main__":
    main()
