from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, description="待分析中文文本")


class PredictResult(BaseModel):
    predicted_label: str
    confidence: float
    positive_score: float
    negative_score: float
    model_name: str
