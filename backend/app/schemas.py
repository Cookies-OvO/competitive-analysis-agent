from pydantic import BaseModel, Field
from datetime import date, datetime


class ProductCreate(BaseModel):
    name: str = Field(..., max_length=200)
    category: str = Field(..., max_length=100)
    brand: str | None = None
    price: float | None = None
    launch_date: date | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    brand: str | None = None
    price: float | None = None
    launch_date: date | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    brand: str | None
    price: float | None
    launch_date: date | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    product_id: int
    user_name: str | None = None
    rating: int = Field(..., ge=1, le=5)
    content: str
    sentiment: str | None = None


class ReviewUpdate(BaseModel):
    user_name: str | None = None
    rating: int | None = None
    content: str | None = None
    sentiment: str | None = None


class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_name: str | None
    rating: int
    content: str
    sentiment: str | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class ReviewTagCreate(BaseModel):
    review_id: int
    tag_name: str = Field(..., max_length=50)
    sentiment: str | None = None
    dimension: str | None = None


class ReviewTagUpdate(BaseModel):
    tag_name: str | None = None
    sentiment: str | None = None
    dimension: str | None = None


class ReviewTagOut(BaseModel):
    id: int
    review_id: int
    tag_name: str
    sentiment: str | None
    dimension: str | None

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: int
    product_id: int
    self_summary: dict | None
    rival_summary: dict | None
    comparison: dict | None
    deep_dive: dict | str | None
    full_report: str | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
