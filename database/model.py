from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Float,
    Text,
    UniqueConstraint,
    CheckConstraint,
    Enum,
    ARRAY
)
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class Role(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG = "org"
    SUB_ORG = "sub_org"
    USER = "user"


class MasterTable(Base):
    __tablename__ = "MasterTable"
    
    tool_id=Column(Integer,primary_key=True,index=True)
    tool_name=Column(String(255),nullable=False,unique=True)
    description=Column(String(300),nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, nullable=True, default=None)


class Admin(Base):
    __tablename__ = "SuperAdmin"

    admin_id = Column(Integer, primary_key=True, index=True)
    admin_name = Column(String(255), nullable=False)
    username = Column(String, nullable=False,unique=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    max_hits = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, nullable=True, default=None)

    organisations = relationship("Organisation", back_populates="admin")


class Organisation(Base):
    __tablename__ = "organisations"

    org_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False,unique=True)
    org_name = Column(String(255), nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    total_hits_limit = Column(Integer, nullable=False)
    available_hits = Column(Integer, nullable=False)
    created_by_admin = Column(
        Integer, ForeignKey("SuperAdmin.admin_id"), nullable=False
    )
    is_active = Column(Boolean, default=True)
    
    tool_ids = Column(ARRAY(Integer), nullable=False, default=[])
    tool_grant_dates = Column(ARRAY(TIMESTAMP(timezone=True)), nullable=False, default=[])
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    


    # Relationships
    admin = relationship("Admin", back_populates="organisations",foreign_keys=[created_by_admin])
    sub_organisations = relationship("SubOrganisation", back_populates="organisation")
    hit_allocation_rules = relationship(
        "HitAllocationRule", back_populates="organisation"
    )

    __table_args__ = (
        CheckConstraint("available_hits >= 0", name="check_available_hits_positive"),
        CheckConstraint("total_hits_limit > 0", name="check_total_hits_positive"),
    )


class SubOrganisation(Base):
    __tablename__ = "sub_organisations"

    sub_org_id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organisations.org_id"), nullable=False)
    username = Column(String, nullable=False,unique=True)
    sub_org_name = Column(String(255), nullable=False)
    is_parent = Column(Boolean, default=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    allocated_hits = Column(Integer, nullable=False)
    remaining_hits = Column(Integer, nullable=False)
    used_hits = Column(Integer, nullable=False)
    
    tool_ids = Column(ARRAY(Integer), nullable=False, default=[])
    tool_grant_dates = Column(ARRAY(TIMESTAMP(timezone=True)), nullable=False, default=[])
    
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    organisation = relationship("Organisation", back_populates="sub_organisations",foreign_keys=[org_id])
    users = relationship("User", back_populates="sub_organisation")
    hit_usage_logs = relationship("HitUsageLog", back_populates="sub_organisation")

    __table_args__ = (
        UniqueConstraint("org_id", "sub_org_id", name="sub_org_id"),
        CheckConstraint("allocated_hits >= 0", name="check_allocated_hits_positive"),
        CheckConstraint("remaining_hits >= 0", name="check_remaining_hits_positive"),
    )


class HitAllocationRule(Base):
    __tablename__ = "hit_allocation_rules"

    rule_id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organisations.org_id"), nullable=False)
    sub_org_id = Column(
        Integer, ForeignKey("sub_organisations.sub_org_id"), nullable=False
    )
    allocation_percentage = Column(Float, nullable=False)
    max_hits = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    organisation = relationship("Organisation", back_populates="hit_allocation_rules")
    sub_organisation = relationship("SubOrganisation")

    __table_args__ = (
        CheckConstraint(
            "allocation_percentage >= 0 AND allocation_percentage <= 100",
            name="check_allocation_percentage_range",
        ),
        CheckConstraint("max_hits >= 0", name="check_max_hits_positive"),
    )


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sub_org_id = Column(
        Integer, ForeignKey("sub_organisations.sub_org_id"), nullable=False
    )
    username = Column(String, nullable=False,unique=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False)
    is_active = Column(Boolean, default=True)
    allocated_hits = Column(Integer, nullable=True,default=0)
    remaninig_hits=Column(Integer,nullable=True,default=0)
    
    tool_ids = Column(ARRAY(Integer), nullable=False, default=[])
    tool_grant_dates = Column(ARRAY(TIMESTAMP(timezone=True)), nullable=False, default=[])

    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    sub_organisation = relationship("SubOrganisation", back_populates="users", foreign_keys=[sub_org_id])



class HitUsageLog(Base):
    __tablename__ = "hit_usage_logs"

    log_id = Column(Integer, primary_key=True)
    sub_org_id = Column(
        Integer, ForeignKey("sub_organisations.sub_org_id"), nullable=False
    )
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    hits_used = Column(Integer, nullable=False)
    usage_timestamp = Column(DateTime, default=func.now(), nullable=False)

    sub_organisation = relationship("SubOrganisation", back_populates="hit_usage_logs")
    user = relationship("User")

    __table_args__ = (
        CheckConstraint("hits_used > 0", name="check_hits_used_positive"),
    )
