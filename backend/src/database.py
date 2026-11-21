import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
engine=create_engine(os.getenv('DATABASE_URL','postgresql+psycopg://resale:resalepass@db/resale'),pool_pre_ping=True)
Session=sessionmaker(engine,expire_on_commit=False)
class Base(DeclarativeBase):pass
