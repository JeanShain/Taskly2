from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "offset_minutes",
            name="uq_task_reminder_offset"
        ),
    )

    id = Column(Integer, primary_key=True)
    task_id = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    offset_minutes = Column(Integer, nullable=False)
    remind_at = Column(DateTime, nullable=False, index=True)

    sent_at = Column(DateTime, nullable=True)
    telegram_message_id = Column(Integer, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    task = relationship("Task", back_populates="reminders")
