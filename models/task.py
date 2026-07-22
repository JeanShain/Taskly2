from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String, Text,)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    priority = Column(
        String(20),
        default="Medium",
        nullable=False
    )
    status = Column(
        String(20),
        default="Pending",
        nullable=False,
        index=True
    )

    deadline = Column(DateTime, nullable=False, index=True)

    # для сумісності зі старою базою
    reminder_sent = Column(
        Boolean,
        default=False,
        nullable=False
    )
    reminder_preset = Column(
        String(30),
        default="default",
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tasks")
    reminders = relationship(
        "Reminder",
        back_populates="task",
        cascade="all, delete-orphan"
    )
