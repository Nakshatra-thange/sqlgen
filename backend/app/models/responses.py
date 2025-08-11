# Pydantic response models
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class DatabaseConnectionResponse(BaseModel):
    id: int
    name: str
    database_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SQLGenerationResponse(BaseModel):
    sql: str
    explanation: str
    confidence: float
    execution_time: float

class TableSchemaResponse(BaseModel):
    table_name: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None 