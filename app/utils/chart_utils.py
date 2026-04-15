from pathlib import Path

import numpy as np


def sentiment_pie_data(positive_count: int, negative_count: int) -> list[dict[str, int | str]]:
    return [
        {"name": "积极", "value": positive_count},
        {"name": "消极", "value": negative_count},
    ]


def confusion_matrix_list(matrix: np.ndarray) -> list[list[int]]:
    return [[int(value) for value in row] for row in matrix.tolist()]


def normalized_path(path: str | Path | None) -> str:
    return "" if not path else str(Path(path))
