"""Pydantic models used by the SafeCart API."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Customer question and optional identifiers used to look up records."""

    query: str = Field(..., description="Customer's question")
    order_id: Optional[str] = Field(default=None, description="Order identifier")
    product_id: Optional[str] = Field(default=None, description="Product identifier")


class ChatResponse(BaseModel):
    """Standard response returned by the chat endpoint."""

    status: str
    response: str
    worker_response: Optional[Dict[str, Any]] = None
    audit: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
