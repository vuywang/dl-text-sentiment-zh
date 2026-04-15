import re


CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")


def clean_text(text: str) -> str:
    value = re.sub(r"\s+", " ", text or "").strip()
    return value


def require_text(text: str) -> str:
    value = clean_text(text)
    if not value:
        raise ValueError("文本内容不能为空")
    if "\ufffd" in value or not CHINESE_CHAR_PATTERN.search(value):
        raise ValueError("请输入包含中文字符的文本")
    return value
