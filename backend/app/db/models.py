import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Current cycle constant — update on universe reset
CURRENT_CYCLE = 5


class Base(DeclarativeBase):
    pass


class Tribe(Base):
    """Local tribe record — maps to World API /v2/tribes/{id}.

    We store our own UUID as PK for internal FK relationships,
    but world_tribe_id links back to the integer ID from the World API.
    """

    __tablename__ = "tribes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    world_tribe_id: Mapped[int | None] = mapped_column(
        Integer, unique=True
    )  # From /v2/tribes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_short: Mapped[str | None] = mapped_column(String(10))  # Ticker e.g. "WOLF"
    leader_address: Mapped[str | None] = mapped_column(
        String(42)
    )  # 0x... wallet address
    invite_code: Mapped[str | None] = mapped_column(String(32), unique=True)
    token_contract_address: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    members: Mapped[list["Member"]] = relationship(
        back_populates="tribe", cascade="all, delete-orphan"
    )
    join_requests: Mapped[list["JoinRequest"]] = relationship(
        back_populates="tribe", cascade="all, delete-orphan"
    )
    production_jobs: Mapped[list["ProductionJob"]] = relationship(
        back_populates="tribe", cascade="all, delete-orphan"
    )
    inventory_items: Mapped[list["TribeInventory"]] = relationship(
        back_populates="tribe", cascade="all, delete-orphan"
    )
    ledger_transactions: Mapped[list["LedgerTransaction"]] = relationship(
        back_populates="tribe", cascade="all, delete-orphan"
    )


class Member(Base):
    """Local member record — maps to World API /v2/smartcharacters/{address}.

    wallet_address is the primary identity (0x hex string from Sui zkLogin).
    character_name comes from the World API "name" field.
    """

    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("tribes.id"))
    wallet_address: Mapped[str] = mapped_column(
        String(42), unique=True, nullable=False
    )  # 0x... hex
    character_name: Mapped[str | None] = mapped_column(String(255))
    smart_character_id: Mapped[str | None] = mapped_column(
        String(100)
    )  # On-chain entity ID (big int)
    role: Mapped[str] = mapped_column(String(50), default="recruit")
    ship_class: Mapped[str | None] = mapped_column(String(100))  # Primary ship class
    timezone: Mapped[str | None] = mapped_column(String(50))
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tribe: Mapped["Tribe | None"] = relationship(back_populates="members")
    assigned_jobs: Mapped[list["ProductionJob"]] = relationship(
        back_populates="assigned_member", foreign_keys="ProductionJob.assigned_to"
    )
    created_jobs: Mapped[list["ProductionJob"]] = relationship(
        back_populates="creator", foreign_keys="ProductionJob.created_by"
    )


class JoinRequest(Base):
    __tablename__ = "join_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tribes.id"))
    wallet_address: Mapped[str] = mapped_column(String(42), nullable=False)
    character_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tribe: Mapped["Tribe"] = relationship(back_populates="join_requests")


class ProductionJob(Base):
    __tablename__ = "production_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tribes.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id"))
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("members.id")
    )
    type_id: Mapped[int | None] = mapped_column(Integer)  # World API type ID
    blueprint_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    materials_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tribe: Mapped["Tribe"] = relationship(back_populates="production_jobs")
    creator: Mapped["Member"] = relationship(
        back_populates="created_jobs", foreign_keys=[created_by]
    )
    assigned_member: Mapped["Member | None"] = relationship(
        back_populates="assigned_jobs", foreign_keys=[assigned_to]
    )


class TribeInventory(Base):
    __tablename__ = "tribe_inventory"
    __table_args__ = (UniqueConstraint("tribe_id", "item_id", name="uq_tribe_item"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tribes.id"))
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)  # World API type ID
    item_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    volume_per_unit: Mapped[float | None] = mapped_column(Float)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("members.id"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tribe: Mapped["Tribe"] = relationship(back_populates="inventory_items")


class LedgerTransaction(Base):
    """Recorded on-chain transaction for tribe treasury tracking."""

    __tablename__ = "ledger_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tribe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tribes.id"))
    tx_digest: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    from_address: Mapped[str] = mapped_column(String(66), nullable=False)
    to_address: Mapped[str] = mapped_column(String(66), nullable=False)
    amount: Mapped[str] = mapped_column(
        String(78), nullable=False
    )  # String for large ints
    coin_type: Mapped[str] = mapped_column(String(255), default="0x2::sui::SUI")
    memo: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="confirmed")
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("members.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tribe: Mapped["Tribe"] = relationship(back_populates="ledger_transactions")


# --- C5: Shroud of Fear ---


class OrbitalZone(Base):
    """Orbital zone with feral AI threat tracking."""

    __tablename__ = "orbital_zones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )  # World API zone identifier
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    coordinates_hash: Mapped[str | None] = mapped_column(
        String(255)
    )  # On-chain location is hashed (location obfuscation, C5+)
    feral_ai_tier: Mapped[int] = mapped_column(Integer, default=0)  # 0-4
    last_scanned: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cycle: Mapped[int] = mapped_column(Integer, default=CURRENT_CYCLE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    feral_events: Mapped[list["FeralAIEvent"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )
    scans: Mapped[list["Scan"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )


class FeralAIEvent(Base):
    """Feral AI evolution event within an orbital zone."""

    __tablename__ = "feral_ai_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("orbital_zones.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # spawned, evolved, critical, dormant
    severity: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    previous_tier: Mapped[int | None] = mapped_column(Integer)
    new_tier: Mapped[int | None] = mapped_column(Integer)
    cycle: Mapped[int] = mapped_column(Integer, default=CURRENT_CYCLE)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    zone: Mapped["OrbitalZone"] = relationship(back_populates="feral_events")


class Scan(Base):
    """Void scan result submitted by a scanner."""

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("orbital_zones.id"), nullable=False
    )
    scanner_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("members.id"))
    result_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # CLEAR, ANOMALY, HOSTILE, UNKNOWN
    result_data: Mapped[str | None] = mapped_column(Text)  # JSON blob
    confidence: Mapped[int] = mapped_column(Integer, default=100)  # 0-100
    cycle: Mapped[int] = mapped_column(Integer, default=CURRENT_CYCLE)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    zone: Mapped["OrbitalZone"] = relationship(back_populates="scans")


class ScanIntel(Base):
    """Aggregated scan intelligence per zone."""

    __tablename__ = "scan_intel"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("orbital_zones.id"), nullable=False
    )
    threat_signature: Mapped[str | None] = mapped_column(String(255))
    anomaly_type: Mapped[str | None] = mapped_column(String(100))
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    cycle: Mapped[int] = mapped_column(Integer, default=CURRENT_CYCLE)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Clone(Base):
    """Clone manufacturing and inventory tracking."""

    __tablename__ = "clones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    clone_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )  # World API clone ID
    owner_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("members.id"))
    blueprint_id: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(
        String(50), default="active"
    )  # active, manufacturing, destroyed
    manufactured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location_zone_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("orbital_zones.id")
    )
    cycle: Mapped[int] = mapped_column(Integer, default=CURRENT_CYCLE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CloneBlueprint(Base):
    """Clone blueprint definitions with material requirements."""

    __tablename__ = "clone_blueprints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    blueprint_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[int] = mapped_column(Integer, default=1)
    materials: Mapped[str | None] = mapped_column(Text)  # JSON
    manufacture_time_sec: Mapped[int] = mapped_column(Integer, default=3600)


class Crown(Base):
    """Crown identity NFT tracking from Sui chain."""

    __tablename__ = "crowns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    crown_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )  # On-chain NFT ID
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("members.id")
    )
    crown_type: Mapped[str] = mapped_column(String(100), nullable=False)
    attributes: Mapped[str | None] = mapped_column(Text)  # JSON
    equipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    chain_tx_id: Mapped[str | None] = mapped_column(String(100))
    cycle: Mapped[int] = mapped_column(Integer, default=CURRENT_CYCLE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
