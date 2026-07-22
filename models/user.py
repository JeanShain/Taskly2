from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)

    # id головного повідомлення taskly2
    interface_message_id = Column(Integer, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    tasks = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan"
    )
