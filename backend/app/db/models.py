from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Date,
    TIMESTAMP,
    JSON,
    Index,
    ForeignKey,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    brand = Column(String(100))
    price = Column(Float)
    launch_date = Column(Date)
    created_at = Column(TIMESTAMP, default=func.now())

    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    reports = relationship("Report", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_name = Column(String(50))
    rating = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    sentiment = Column(String(10))
    created_at = Column(TIMESTAMP, default=func.now())

    product = relationship("Product", back_populates="reviews")
    tags = relationship("ReviewTag", back_populates="review", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_r_product", "product_id"),
        Index("idx_r_rating", "rating"),
    )


class ReviewTag(Base):
    __tablename__ = "review_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    tag_name = Column(String(50), nullable=False)
    sentiment = Column(String(10))
    dimension = Column(String(50))

    review = relationship("Review", back_populates="tags")

    __table_args__ = (
        Index("idx_t_dim", "dimension"),
    )


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    self_summary = Column(JSON)
    rival_summary = Column(JSON)
    comparison = Column(JSON)
    deep_dive = Column(JSON)
    full_report = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())
