import argparse
import json
import random
import sys
from datetime import datetime
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
from app.models.db.train_task import TrainTask  # noqa: E402
from app.utils.time_utils import now_str  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="训练中文文本情感二分类模型")
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument("--epoch", type=int, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--learning-rate", type=float, required=True)
    parser.add_argument("--max-length", type=int, required=True)
    parser.add_argument("--model-name", type=str, required=True)
    parser.add_argument("--train-limit", type=int, default=0)
    parser.add_argument("--eval-limit", type=int, default=0)
    return parser.parse_args()


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


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


def evaluate(model, data_loader: DataLoader, device: torch.device) -> dict[str, object]:
    model.eval()
    total_loss = 0.0
    total_batches = 0
    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for batch in data_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            total_loss += float(outputs.loss.item())
            total_batches += 1
            preds = torch.argmax(outputs.logits, dim=-1)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(batch["labels"].cpu().tolist())

    matrix = confusion_matrix(all_labels, all_preds, labels=[0, 1])
    return {
        "val_loss": total_loss / max(total_batches, 1),
        "accuracy": accuracy_score(all_labels, all_preds),
        "precision_score": precision_score(all_labels, all_preds, zero_division=0),
        "recall_score": recall_score(all_labels, all_preds, zero_division=0),
        "f1_score": f1_score(all_labels, all_preds, zero_division=0),
        "confusion_matrix": matrix,
    }


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


def plot_loss_curve(train_losses: list[float], val_losses: list[float], output_path: Path) -> None:
    plt.figure(figsize=(6, 4))
    epochs = list(range(1, len(train_losses) + 1))
    plt.plot(epochs, train_losses, marker="o", label="训练损失")
    plt.plot(epochs, val_losses, marker="s", label="验证损失")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("训练损失曲线")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def train(args: argparse.Namespace, output_dir: Path) -> dict[str, object]:
    set_seed()
    dataset = load_dataset(settings.DATASET_HF_ID, cache_dir=str(settings.DATASET_DIR))
    train_dataset = dataset["train"]
    eval_split = "validation" if "validation" in dataset else "test"
    eval_dataset = dataset[eval_split]
    if args.train_limit > 0:
        train_dataset = train_dataset.shuffle(seed=42).select(range(min(args.train_limit, len(train_dataset))))
    if args.eval_limit > 0:
        eval_dataset = eval_dataset.shuffle(seed=42).select(range(min(args.eval_limit, len(eval_dataset))))

    tokenizer = AutoTokenizer.from_pretrained(settings.PRETRAINED_MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        settings.PRETRAINED_MODEL_NAME,
        num_labels=2,
    )
    model.config.id2label = {0: "消极", 1: "积极"}
    model.config.label2id = {"消极": 0, "积极": 1}

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        collate_fn=lambda batch: collate_batch(batch, tokenizer, args.max_length),
    )
    eval_loader = DataLoader(
        eval_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        collate_fn=lambda batch: collate_batch(batch, tokenizer, args.max_length),
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    train_losses: list[float] = []
    val_losses: list[float] = []
    latest_metrics: dict[str, object] = {}

    for epoch_index in range(args.epoch):
        model.train()
        total_loss = 0.0
        total_batches = 0
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())
            total_batches += 1

        train_loss = total_loss / max(total_batches, 1)
        latest_metrics = evaluate(model, eval_loader, device)
        train_losses.append(train_loss)
        val_losses.append(float(latest_metrics["val_loss"]))
        print(
            f"epoch={epoch_index + 1}, train_loss={train_loss:.6f}, "
            f"val_loss={float(latest_metrics['val_loss']):.6f}, "
            f"accuracy={float(latest_metrics['accuracy']):.6f}",
            flush=True,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer.save_pretrained(output_dir)
    model.save_pretrained(output_dir)

    confusion_matrix_path = output_dir / "confusion_matrix.png"
    loss_curve_path = output_dir / "loss_curve.png"
    plot_confusion_matrix(latest_metrics["confusion_matrix"], confusion_matrix_path)
    plot_loss_curve(train_losses, val_losses, loss_curve_path)

    metrics = {
        "train_loss": train_losses[-1],
        "val_loss": val_losses[-1],
        "accuracy": float(latest_metrics["accuracy"]),
        "precision_score": float(latest_metrics["precision_score"]),
        "recall_score": float(latest_metrics["recall_score"]),
        "f1_score": float(latest_metrics["f1_score"]),
        "confusion_matrix": latest_metrics["confusion_matrix"].tolist(),
        "confusion_matrix_path": str(confusion_matrix_path),
        "loss_curve_path": str(loss_curve_path),
    }
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)
    with (output_dir / "train_config.json").open("w", encoding="utf-8") as file:
        json.dump(
            {
                "model_name": args.model_name,
                "pretrained_model": settings.PRETRAINED_MODEL_NAME,
                "dataset": settings.DATASET_NAME,
                "epoch": args.epoch,
                "batch_size": args.batch_size,
                "learning_rate": args.learning_rate,
                "max_length": args.max_length,
                "train_limit": args.train_limit,
                "eval_limit": args.eval_limit,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )
    return metrics


def main() -> None:
    args = parse_args()
    init_db()
    output_dir = settings.ARCHIVE_MODEL_DIR / f"task_{args.task_id}_{now_str()}"
    db = SessionLocal()
    try:
        task = db.get(TrainTask, args.task_id)
        if task is None:
            raise RuntimeError(f"训练任务不存在：{args.task_id}")
        metrics = train(args, output_dir)

        task.train_loss = float(metrics["train_loss"])
        task.val_loss = float(metrics["val_loss"])
        task.accuracy = float(metrics["accuracy"])
        task.precision_score = float(metrics["precision_score"])
        task.recall_score = float(metrics["recall_score"])
        task.f1_score = float(metrics["f1_score"])
        task.confusion_matrix_path = str(metrics["confusion_matrix_path"])
        task.model_dir = str(output_dir)
        task.status = "completed"
        task.finished_at = datetime.now()

        db.query(ModelRegistry).update({ModelRegistry.is_active: False})
        db.add(
            ModelRegistry(
                model_name=args.model_name,
                model_type="finetuned",
                model_dir=str(output_dir),
                is_active=True,
                remark="ChnSentiCorp 微调后的中文情感二分类模型。",
            )
        )
        db.commit()
        print(f"训练完成，模型目录：{output_dir}", flush=True)
    except Exception:
        task = db.get(TrainTask, args.task_id)
        if task is not None:
            task.status = "failed"
            task.finished_at = datetime.now()
            db.commit()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
