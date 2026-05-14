from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ParticipantStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class EventStatus(enum.Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ServerConfig(Base):
    __tablename__ = "server_configs"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    panel_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    panel_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    appointment_types: Mapped[list[AppointmentType]] = relationship(
        back_populates="server_config", cascade="all, delete-orphan"
    )


class AppointmentType(Base):
    __tablename__ = "appointment_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("server_configs.guild_id"))
    label: Mapped[str] = mapped_column(String(80))
    required_creator_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    restrict_invitees_to_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    server_config: Mapped[ServerConfig] = relationship(back_populates="appointment_types")
    events: Mapped[list[Event]] = relationship(back_populates="appointment_type")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger)
    creator_id: Mapped[int] = mapped_column(BigInteger)
    appointment_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointment_types.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(2000), default="")
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.OPEN)
    # use_alter breaks the circular FK cycle between events ↔ time_slots
    confirmed_slot_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("time_slots.id", use_alter=True, name="fk_event_confirmed_slot"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    appointment_type: Mapped[AppointmentType] = relationship(back_populates="events")
    time_slots: Mapped[list[TimeSlot]] = relationship(
        back_populates="event",
        foreign_keys="TimeSlot.event_id",
        cascade="all, delete-orphan",
    )
    participants: Mapped[list[Participant]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime)

    event: Mapped[Event] = relationship(back_populates="time_slots", foreign_keys=[event_id])
    votes: Mapped[list[TimeSlotVote]] = relationship(
        back_populates="time_slot", cascade="all, delete-orphan"
    )


class Participant(Base):
    __tablename__ = "participants"

    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(ParticipantStatus), default=ParticipantStatus.PENDING
    )

    event: Mapped[Event] = relationship(back_populates="participants")


class TimeSlotVote(Base):
    __tablename__ = "time_slot_votes"

    time_slot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("time_slots.id"), primary_key=True
    )
    participant_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer)
    available: Mapped[bool] = mapped_column(Boolean, default=False)

    time_slot: Mapped[TimeSlot] = relationship(back_populates="votes")
