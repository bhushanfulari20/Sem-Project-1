"""Pydantic models used by the SafeCart API."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Customer question and optional identifiers used to look up records."""

    query: str = Field(..., description="Customer's question")
    order_id: Optional[str] = Field(default=None, description="Order identifier")
    product_id: Optional[str] = Field(default=None, description="Product identifier")
    customer_name: Optional[str] = Field(default=None, description="Logged-in customer name")
    user_id: Optional[str] = Field(default=None, description="Logged-in customer user ID")
    customer_email: Optional[str] = Field(default=None, description="Logged-in customer email")
    action: Optional[str] = Field(default=None, description="Optional action like CONFIRM_ORDER")


class ChatResponse(BaseModel):
    """Standard response returned by the chat endpoint."""

    status: str
    response: str
    worker_response: Optional[Dict[str, Any]] = None
    audit: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class OrderCreateRequest(BaseModel):
    product_id: str
    customer_name: Optional[str] = "Amazon Customer"
    customer_email: Optional[str] = None
    shipping_address: Optional[str] = "India"
    quantity: Optional[int] = 1


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    address: Optional[str] = "India"


class CartItemRequest(BaseModel):
    product_id: str
    quantity: Optional[int] = 1


class CheckoutItem(BaseModel):
    product_id: str
    quantity: Optional[int] = 1


class CheckoutRequest(BaseModel):
    items: list[CheckoutItem]
    customer_name: Optional[str] = "Amazon Customer"
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[str] = "India"
    payment_method: Optional[str] = "Simulated Demo Payment"
    is_demo: Optional[bool] = True


class ProductCreateRequest(BaseModel):
    product_id: Optional[str] = None
    product_name: str
    category: str
    price: float
    description: Optional[str] = ""
    initial_stock: Optional[int] = 10
    image_url: Optional[str] = None


class ProductUpdateRequest(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    image_url: Optional[str] = None


class StockUpdateRequest(BaseModel):
    quantity: int


