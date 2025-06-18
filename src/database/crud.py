from sqlalchemy.orm import Session
from . import models
from typing import List, Optional, Dict, Any

# Restaurant CRUD operations
def create_restaurant(db: Session, restaurant_data: Dict[str, Any]) -> models.Restaurant:
    db_restaurant = models.Restaurant(**restaurant_data)
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def get_restaurant(db: Session, restaurant_id: int) -> Optional[models.Restaurant]:
    return db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()

def get_restaurant_by_name(db: Session, name: str) -> Optional[models.Restaurant]:
    return db.query(models.Restaurant).filter(models.Restaurant.name == name).first()

def get_restaurant_by_address(db: Session, address: str) -> Optional[models.Restaurant]:
    return db.query(models.Restaurant).filter(models.Restaurant.address == address).first()

def get_restaurants(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.Restaurant]:
    return db.query(models.Restaurant).offset(skip).limit(limit).all()

def update_restaurant(
    db: Session, 
    restaurant_id: int, 
    restaurant_data: Dict[str, Any]
) -> Optional[models.Restaurant]:
    db_restaurant = get_restaurant(db, restaurant_id)
    if db_restaurant:
        for key, value in restaurant_data.items():
            setattr(db_restaurant, key, value)
        db.commit()
        db.refresh(db_restaurant)
    return db_restaurant

def delete_restaurant(db: Session, restaurant_id: int) -> bool:
    db_restaurant = get_restaurant(db, restaurant_id)
    if db_restaurant:
        db.delete(db_restaurant)
        db.commit()
        return True
    return False

# RestaurantLLMInfo CRUD operations
def create_llm_info(
    db: Session, 
    restaurant_id: int, 
    llm_info_data: Dict[str, Any]
) -> models.RestaurantLLMInfo:
    # Ensure restaurant exists
    if not get_restaurant(db, restaurant_id):
        raise ValueError(f"Restaurant with id {restaurant_id} does not exist")
    
    # Check if LLM info already exists
    existing_info = get_llm_info(db, restaurant_id)
    if existing_info:
        return update_llm_info(db, restaurant_id, llm_info_data)
    
    # Create new LLM info
    llm_info_data['restaurant_id'] = restaurant_id
    db_llm_info = models.RestaurantLLMInfo(**llm_info_data)
    db.add(db_llm_info)
    db.commit()
    db.refresh(db_llm_info)
    return db_llm_info

def get_llm_info(db: Session, restaurant_id: int) -> Optional[models.RestaurantLLMInfo]:
    return db.query(models.RestaurantLLMInfo).filter(
        models.RestaurantLLMInfo.restaurant_id == restaurant_id
    ).first()

def update_llm_info(
    db: Session, 
    restaurant_id: int, 
    llm_info_data: Dict[str, Any]
) -> Optional[models.RestaurantLLMInfo]:
    db_llm_info = get_llm_info(db, restaurant_id)
    if db_llm_info:
        for key, value in llm_info_data.items():
            setattr(db_llm_info, key, value)
        db.commit()
        db.refresh(db_llm_info)
    return db_llm_info

def delete_llm_info(db: Session, restaurant_id: int) -> bool:
    db_llm_info = get_llm_info(db, restaurant_id)
    if db_llm_info:
        db.delete(db_llm_info)
        db.commit()
        return True
    return False

# Combined operations
def get_restaurant_with_llm_info(
    db: Session, 
    restaurant_id: int
) -> Optional[models.Restaurant]:
    """Get a restaurant with its LLM info in a single query."""
    return db.query(models.Restaurant).filter(
        models.Restaurant.id == restaurant_id
    ).first()

def get_all_restaurants_with_llm_info(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Restaurant]:
    """Get all restaurants with their LLM info in a single query."""
    return db.query(models.Restaurant).offset(skip).limit(limit).all() 