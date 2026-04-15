from pydantic import BaseModel


class BatchTaskResponse(BaseModel):
    id: int
    original_file_name: str
    total_count: int
    positive_count: int
    negative_count: int
    result_file_path: str | None
    status: str
