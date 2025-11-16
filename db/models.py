from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Float, ARRAY, Boolean, Enum as SqlEnum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class Language(enum.Enum):
    EN = "en"
    UA = "ua"
    RU = "ru"


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    language = Column(SqlEnum(Language), default=Language.UA)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_action = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lead = Column(String(255), default="")
    avg_budget = Column(Float, default=0.0)
    reason_decline = Column(String(255))
    response_time = Column(Float, default=0.0)

    context_msg_id = Column(Integer, default=0)
    context_reply_id = Column(Integer, default=0)
    

    messages = relationship("Messages", back_populates="user", cascade="all, delete")
    requested_apartments = relationship("RequestedApartment", back_populates="user", cascade="all, delete")


class Messages(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(255), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", back_populates="messages")

    replies = relationship("Replies", back_populates="message", cascade="all, delete")


class Replies(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    reply = Column(String(2555), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Messages", back_populates="replies")


class RequestedApartment(Base):
    __tablename__ = "requested_apartments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(255), nullable=True, default=None)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    district_ids = Column(ARRAY(Integer), nullable=True, default=None)
    microarea_ids = Column(ARRAY(Integer), nullable=True, default=None)
    street_ids = Column(ARRAY(Integer), nullable=True, default=None)
    condition_in = Column(ARRAY(Integer), nullable=True, default=None)
    rooms_in = Column(ARRAY(Integer), nullable=True, default=None)
    price_min = Column(Float, nullable=True, default=None)
    price_max = Column(Float, nullable=True, default=None)
    area_min = Column(Float, nullable=True, default=None)
    area_max = Column(Float, nullable=True, default=None)
    floor_min = Column(Integer, nullable=True, default=None)
    floor_max = Column(Integer, nullable=True, default=None)
    floors_total_max = Column(Integer, nullable=True, default=None)
    lat = Column(Float, nullable=True, default=None)
    lon = Column(Float, nullable=True, default=None)
    radius_km = Column(Float, nullable=True, default=None)
    appartment_ids = Column(ARRAY(Integer), nullable=True, default=None)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", back_populates="requested_apartments")
    
