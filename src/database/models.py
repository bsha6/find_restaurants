from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Restaurant(Base):
    __tablename__ = "Restaurant"  # Note: SQLite is case-sensitive for table names

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    address = Column(Text, nullable=False)
    source = Column(Text)
    source_url = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationship to LLM info
    llm_info = relationship("RestaurantLLMInfo", back_populates="restaurant", uselist=False)

class RestaurantLLMInfo(Base):
    __tablename__ = "RestaurantLLMInfo"
    
    restaurant_id = Column(Integer, ForeignKey("Restaurant.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    cuisine = Column(Text)
    vibe = Column(Text)
    llm_model_version = Column(Text)
    generated_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Relationship back to Restaurant
    restaurant = relationship("Restaurant", back_populates="llm_info") 