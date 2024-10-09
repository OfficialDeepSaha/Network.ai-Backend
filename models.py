from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    bio = Column(String)
    education = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    twitter_handle = Column(String)
    about = Column(String)
    github= Column(String)
    linkedin= Column(String)
    banner_image= Column(String)
    profile_image= Column(String)
    embedding = Column(JSON, nullable=True)
    
    # Define relationships
    group_chats = relationship("GroupChat", secondary="group_chat_members", back_populates="members")
    sent_requests = relationship("ConnectionRequest", foreign_keys='ConnectionRequest.sender_id', back_populates="sender")
    received_requests = relationship("ConnectionRequest", foreign_keys='ConnectionRequest.receiver_id', back_populates="receiver")

    sent_requests_for_group = relationship("GroupRequest", foreign_keys='GroupRequest.sender_id' , back_populates="sender")
    received_requests_for_group = relationship("GroupRequest", foreign_keys="[GroupRequest.receiver_id]", back_populates="receiver")
    
    # Add the inverse relationship for Agent
    agents = relationship("Agent", back_populates="user")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    file_path = Column(String)


class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)  # Added ForeignKey constraint
    state = Column(Text, nullable=True)  # Store state as JSON or string
    last_active = Column(String)  # Use ISO format for timestamps
    next_action = Column(String, nullable=True)
    update_knowledge = Column(JSON, nullable=True)
    # Define relationship with User
    user = relationship("User", back_populates="agents")



class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    feedback_text = Column(Text)
    rating = Column(Integer)




class GroupChat(Base):
    __tablename__ = 'group_chats'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("User", secondary="group_chat_members", back_populates="group_chats")
    messages = relationship("GroupChatMessage", back_populates="chat")

class GroupChatMember(Base):
    __tablename__ = 'group_chat_members'
    group_chat_id = Column(Integer, ForeignKey('group_chats.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

class GroupChatMessage(Base):
    __tablename__ = 'group_chat_messages'
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('group_chats.id'))
    sender_id = Column(Integer, ForeignKey('users.id'))
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("GroupChat", back_populates="messages")
    sender = relationship("User")


class UserFeedback(Base):
    __tablename__ = 'user_feedback'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    recommended_user_id = Column(Integer, ForeignKey('users.id'))
    feedback = Column(String)  # e.g., 'positive', 'negative', 'neutral'
    score = Column(Float)  # A numeric score or rating for the recommendation

    user = relationship("User", foreign_keys=[user_id])
    recommended_user = relationship("User", foreign_keys=[recommended_user_id])




class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

class ChatResponse(BaseModel):
    id: int
    user_1_id: int
    user_2_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, index=True)
    user_1_id = Column(Integer, ForeignKey('users.id'))
    user_2_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    user_1 = relationship("User", foreign_keys=[user_1_id])
    user_2 = relationship("User", foreign_keys=[user_2_id])
    messages = relationship('Message', back_populates='chat')  # Establish relationship


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    sender_id = Column(Integer, ForeignKey('users.id'))
    content = Column(String, nullable=False)  # Message content (text or emoji)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship('Chat', back_populates='messages')
    sender = relationship('User', foreign_keys=[sender_id])



DATABASE_URL = "postgresql://postgres:VKTbOKIJLfiXXbIBOjddyXDQuPLqmySH@postgres.railway.internal:5432/railway"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
