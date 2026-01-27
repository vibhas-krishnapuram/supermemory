from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Text, Boolean, Enum, DateTime
from sqlalchemy.orm import Mapped, sessionmaker, mapped_column, declarative_base, relationship

from db.database import Base
from datetime import datetime
import enum 

class CallOutcome(enum.Enum):
    SUCCESSFUL = "SUCCESSFUL"
    CALLBACK = "CALLBACK"
    NOT_INTERESTED = "NOT_INTERESTED"
    MISSED = "MISSED"


class Task_Manager(Base):
    __tablename__ = "taskmanager"

    call_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_error: Mapped[str] = mapped_column(Text, nullable=True)

    outcome: Mapped[CallOutcome] = mapped_column(
        Enum(CallOutcome),
        nullable=True,
        index=True
    )

    callback_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )


    def __repr__(self):
        return f"<TaskManager(call_id={self.call_id}, phone={self.phone}, processed={self.processed})>"

