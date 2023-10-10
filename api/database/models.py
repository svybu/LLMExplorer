from sqlalchemy import Column, Integer, String, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import DateTime

Base = declarative_base()

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column('crated_at', DateTime, default=func.now())
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
    plus = Column(Boolean, default=False)  # Додано поле для преміум акаунту

    # Відносини до інших таблиць
    chat_histories = relationship("ChatHistory", back_populates="user")
    documents = relationship("Document", back_populates="user")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    user_message = Column(String)
    bot_message = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))  # Foreign key to User table

    # Відносини до інших таблиць
    user = relationship("User", back_populates="chat_histories")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # Текст документу
    uploaded_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))  # Foreign key to User table

    # Відносини до інших таблиць
    user = relationship("User", back_populates="documents")
