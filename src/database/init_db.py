from .database import get_engine
from . import models

def init_db():
    engine = get_engine()
    models.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully!") 