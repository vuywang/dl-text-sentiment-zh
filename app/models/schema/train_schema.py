from pydantic import BaseModel, Field


class TrainStartRequest(BaseModel):
    epoch: int = Field(1, ge=1, le=20)
    batch_size: int = Field(8, ge=1, le=128)
    learning_rate: float = Field(2e-5, gt=0, le=1)
    max_length: int = Field(128, ge=16, le=512)


class TrainTaskResponse(BaseModel):
    id: int
    model_name: str
    dataset_name: str
    epoch_count: int
    batch_size: int
    learning_rate: float
    max_length: int
    status: str
