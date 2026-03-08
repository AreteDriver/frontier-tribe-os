import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Tribe(Base):
    __tablename__ = "tribes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    leader_character_id: Mapped[str | None] = mapped_column(String(100))
    invite_code: Mapped[str | None] = mapped_column(String(32), unique=True)
    token_contract_address: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    members: Mapped[list["Member"]] = relationship(back_populates="tribe", cascade="all, delete-orphan")
    join_requests: Mapped[list["JoinRequest"]] = relationship(back_populates="tribe", cascade="all, delete-orphan")
    production_jobs: Mapped[list["ProductionJob"]] = relationship(back_populates="tribe", cascade="all, delete-orphan")
    inventory_items: Mapped[list["TribeInventory"]] = relationship(back_populates="tribe", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tribes.id"))
    character_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    character_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="recruit")
    timezone: Mapped[str | None] = mapped_column(String(50))
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tribe: Mapped["Tribe"] = relationship(back_populates="members")
    assigned_jobs: Mapped[list["ProductionJob"]] = relationship(back_populates="assigned_member")


class JoinRequest(Base):
    __tablename__ = "join_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tribes.id"))
    character_id: Mapped[str] = mapped_column(String(100), nullable=False)
    character_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tribe: Mapped["Tribe"] = relationship(back_populates="join_requests")


class ProductionJob(Base):
    __tablename__ = "production_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tribes.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("members.id"))
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("members.id"))
    blueprint_id: Mapped[str | None] = mapped_column(String(100))
    blueprint_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    materials_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tribe: Mapped["Tribe"] = relationship(back_populates="production_jobs")
    assigned_member: Mapped["Member | None"] = relationship(back_populates="assigned_jobs", foreign_keys=[assigned_to])


class TribeInventory(Base):
    __tablename__ = "tribe_inventory"
    __table_args__ = (UniqueConstraint("tribe_id", "item_id", name="uq_tribe_item"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tribes.id"))
    item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    item_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("members.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tribe: Mapped["Tribe"] = relationship(back_populates="inventory_items")
