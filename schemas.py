from pydantic import BaseModel
from typing import ClassVar, Optional, List
from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from models import Base

# User schemas
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    bio: str


class UserUpdate(BaseModel):
    user_id: int
    education: Optional[str] = None
    experience: Optional[str] = None
    goal: Optional[str] = None
    twitter_handle: Optional[str] = None
    bio: Optional[str] = None
    about: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    banner_image: Optional[str] = None
    profile_image: Optional[str] = None



class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    bio: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    goal: Optional[str] = None
    twitter_handle: Optional[str] = None
    about: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    banner_image: Optional[str] = None
    profile_image: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True  # This enables `from_orm` functionality


# Agent schema
class AgentModel(BaseModel):
    user_id: int
    state: Optional[str] = "initial"
    last_active: Optional[datetime] = None
    next_action: Optional[str] = None
    update_knowledge: Optional[List[float]] = None  # Assuming embeddings are a list of floats 

    class Config:
        orm_mode = True


# Feedback schema
class FeedbackCreate(BaseModel):
    user_id: int
    text: str
    rating: int




# Approval request schemas
class ApprovalRequestCreate(BaseModel):
    user_id: int
    action: str
    target_user_id: int

   
# Define GroupChat schemas
class GroupChatCreate(BaseModel):
    name: str
    members: List[int]  # List of user IDs to include in the group

class GroupChatResponse(BaseModel):
    id: Optional[int] = None
    name: str
    created_at: Optional[datetime] = None
    members: List[UserResponse]  # Ensure UserResponse is defined and imported

class GroupChatMessageCreate(BaseModel):
    chat_id: int
    sender_id: int
    content: str

class GroupChatMessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

class ApprovalRequest(BaseModel):
    approved: bool



# Define your enum
class ConnectionStatus(PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class GroupRequestStatus(PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ActionEnum(PyEnum):
    CONNECTION_REQUEST = 'connection_request'
    GROUP_CREATION = 'group_creation'
    START_CONVERSATION = 'start_conversation'    

# Define the SQLAlchemy model
class ConnectionRequest(Base):
    __tablename__ = 'connection_requests'

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    action = Column(Enum(ActionEnum), nullable=False) # Add this line
    # Use SQLAlchemy's Enum class with the Python enum
    status = Column(Enum(ConnectionStatus, values_callable=lambda x: [e.value for e in x]), default=ConnectionStatus.PENDING.value)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_requests", overlaps="sent_requests")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_requests", overlaps="received_requests")






class GroupRequest(Base):
    __tablename__ = 'group_requests'

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    target_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    action = Column(Enum(ActionEnum), nullable=False) # Add this line
    # Use SQLAlchemy's Enum class with the Python enum
    status = Column(Enum(GroupRequestStatus, values_callable=lambda x: [e.value for e in x]), default=GroupRequestStatus.PENDING.value)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_requests_for_group", overlaps="sent_requests_for_group")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_requests_for_group", overlaps="received_requests_for_group")    



class Connection(Base):
    __tablename__ = "connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id_1 = Column(Integer, ForeignKey("users.id"))
    user_id_2 = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# Subscription Model
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_id = Column(String, nullable=False)
    plan_type = Column(String, nullable=False)  # E.g., "Free", "Pro"
    created_at =Column(DateTime, default=datetime.utcnow)

    # You can define a relationship to the User model if needed
    





class ConnectionRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    sender_name: str  # Add this line
    status: ConnectionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None  # updated_at may not be present if not updated

    class Config:
        use_enum_values = True  # To use enum values directly in the response     


class GroupRequestResponse(BaseModel):

    id:int
    sender_id: int
    receiver_id: int
    sender_name: str  # Add this line
    target_user_id: int
    status: ConnectionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None  # updated_at may not be present if not updated

    class Config:
        use_enum_values = True  # To use enum values directly in the response   

        



# ConversationStatus Enum
class ConversationStatus(PyEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    UNRESOLVED = "unresolved"


# Conversation Model
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    states = relationship("ConversationState", back_populates="conversation")


# ConversationState Model
class ConversationState(Base):
    __tablename__ = 'conversation_states'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))  # Ensure this column exists
    agent_a_id = Column(Integer, ForeignKey('users.id'))
    agent_b_id = Column(Integer, ForeignKey('users.id'))
    status = Column(Enum(ConversationStatus), default=ConversationStatus.IN_PROGRESS)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    outcome = Column(String, nullable=True)

    conversation = relationship("Conversation", back_populates="states")
    agent_a = relationship("User", foreign_keys=[agent_a_id])
    agent_b = relationship("User", foreign_keys=[agent_b_id])
    history = relationship("ConversationHistory", back_populates="conversation_state", cascade="all, delete-orphan")




# ConversationHistory Model
class ConversationHistory(Base):
    __tablename__ = 'conversation_history'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversation_states.id'))
    sender_id = Column(Integer, ForeignKey('users.id'))
    receiver_id = Column(Integer, ForeignKey('users.id'))
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Define relationship to ConversationState
    conversation_state = relationship("ConversationState", back_populates="history")
    
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])