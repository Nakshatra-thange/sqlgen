# Database models
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DatabaseConnection(Base):
    __tablename__ = "database_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    connection_string = Column(Text)
    database_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GeneratedQuery(Base):
    __tablename__ = "generated_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    natural_language_query = Column(Text)
    generated_sql = Column(Text)
    database_connection_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow) 