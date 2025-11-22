from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Dict, Any

# Ingestion DTO
class TransactionDTO(BaseModel):
    date: date
    description: str
    amount: float
    category: str
    type: str
    raw_data: str

# API Chat DTOs
class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str = Field(..., example="What is the profit ratio for Q1?")
    history: List[Message] = Field(default=[], description="Conversation history for context")

class QueryResponse(BaseModel):
    answer: str
    data_points: List[Dict[str, Any]]
    generated_sql: str