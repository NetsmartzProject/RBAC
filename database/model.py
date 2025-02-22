from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    CheckConstraint,
    Enum,
    ARRAY,
    UUID
)
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()


class Role(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG = "org"
    SUB_ORG = "sub_org"
    USER = "user"


class ToolMaster(Base):
    __tablename__ = "ToolMaster"
    tool_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    tool_name=Column(String(255),nullable=False,unique=True)
    description=Column(String(300),nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class Admin(Base):
    __tablename__ = "SuperAdmin"
    admin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    admin_name = Column(String(255), nullable=False)
    username = Column(String, nullable=False,unique=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, nullable=False, onupdate=func.now())
    organisations = relationship("Organisation", back_populates="admin")


class Organisation(Base):
    __tablename__ = "organisations"
    org_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    username = Column(String, nullable=False,unique=True)
    org_name = Column(String(255), nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    allocated_hits = Column(Integer, nullable=False)
    available_hits = Column(Integer, nullable=False)
    used_hits = Column(Integer, nullable=True, default=0)
    allocated_ai_tokens = Column(Integer, nullable=True)
    remaining_ai_tokens=Column(Integer, nullable=True)
    used_ai_tokens = Column(Integer, nullable=False, default=0)
    created_by_admin = Column(
        UUID, ForeignKey("SuperAdmin.admin_id"), nullable=False
    )
    tool_ids = Column(ARRAY(UUID), nullable=False, default=[])
    tool_grant_dates = Column(ARRAY(TIMESTAMP(timezone=True)), nullable=False, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    admin = relationship("Admin", back_populates="organisations",foreign_keys=[created_by_admin])
    sub_organisations = relationship("SubOrganisation", back_populates="organisation")
    __table_args__ = (
        CheckConstraint("allocated_hits >= 0", name="check_total_hits_positive"),
        CheckConstraint("available_hits >= 0", name="check_available_hits_positive"),
        CheckConstraint("allocated_ai_tokens >= 0", name="check_allocated_ai_tokens"),
        CheckConstraint("remaining_ai_tokens >= 0", name="check_available_ai_tokens")
    )

class SubOrganisation(Base):
    __tablename__ = "sub_organisations"
    sub_org_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    org_id = Column(UUID, ForeignKey("organisations.org_id"), nullable=False)
    username = Column(String, nullable=False,unique=True)
    sub_org_name = Column(String(255), nullable=False)
    is_parent = Column(Boolean, default=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    allocated_hits = Column(Integer, nullable=False)
    available_hits = Column(Integer, nullable=False)
    used_hits = Column(Integer, nullable=True, default=0)
    allocated_ai_tokens = Column(Integer, nullable=True)
    remaining_ai_tokens=Column(Integer, nullable=True)
    used_ai_tokens = Column(Integer, nullable=False, default=0)
    tool_ids = Column(ARRAY(UUID), nullable=False, default=[])
    tool_grant_dates = Column(ARRAY(TIMESTAMP(timezone=True)), nullable=False, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    organisation = relationship("Organisation", back_populates="sub_organisations",foreign_keys=[org_id])
    users = relationship("User", back_populates="sub_organisation")

    __table_args__ = (
        CheckConstraint("allocated_hits >= 0", name="check_total_hits_positive"),
        CheckConstraint("available_hits >= 0", name="check_available_hits_positive"),
        CheckConstraint("allocated_ai_tokens >= 0", name="check_allocated_ai_tokens"),
        CheckConstraint("remaining_ai_tokens >= 0", name="check_available_ai_tokens")
    )

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    sub_org_id = Column(
        UUID, ForeignKey("sub_organisations.sub_org_id"), nullable=False
    )
    username = Column(String, nullable=False,unique=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False)
    
    allocated_hits = Column(Integer, nullable=False)
    available_hits = Column(Integer, nullable=False)
    used_hits = Column(Integer, nullable=True,default=0)

    allocated_ai_tokens = Column(Integer, nullable=True,default=0)
    remaining_ai_tokens=Column(Integer,nullable=True,default=0)
    used_ai_tokens = Column(Integer, nullable=True,default=0)

    tool_ids = Column(ARRAY(UUID), nullable=False, default=[])
    tool_grant_dates = Column(ARRAY(TIMESTAMP(timezone=True)), nullable=False, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    sub_organisation = relationship("SubOrganisation", back_populates="users", foreign_keys=[sub_org_id])

    __table_args__ = (
        CheckConstraint("allocated_hits >= 0", name="check_total_hits_positive"),
        CheckConstraint("available_hits >= 0", name="check_available_hits_positive"),
        CheckConstraint("allocated_ai_tokens >= 0", name="check_allocated_ai_tokens"),
        CheckConstraint("remaining_ai_tokens >= 0", name="check_available_ai_tokens")
    )