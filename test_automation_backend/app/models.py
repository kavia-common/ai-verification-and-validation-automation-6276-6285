from datetime import datetime
from typing import Optional
from sqlalchemy import func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from .extensions import db


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete flag."""
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True, server_default=db.text("1"))


class SRS(db.Model, TimestampMixin, SoftDeleteMixin):
    """Top-level SRS entity (a document with potentially many versions)."""
    __tablename__ = "srs"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text)
    uploaded_by: Mapped[Optional[str]] = mapped_column(db.String(128))

    # Relationships
    versions: Mapped[list["SRSVersion"]] = relationship(
        "SRSVersion", back_populates="srs", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_srs_name", "name"),
    )


class SRSVersion(db.Model, TimestampMixin, SoftDeleteMixin):
    """A version of an SRS document; each upload becomes a new version."""
    __tablename__ = "srs_versions"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    srs_id: Mapped[int] = mapped_column(db.ForeignKey("srs.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(db.String(1024), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(db.String(256))
    notes: Mapped[Optional[str]] = mapped_column(db.Text)

    srs: Mapped[SRS] = relationship("SRS", back_populates="versions")
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="srs_version", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("srs_id", "version", name="uq_srs_version_per_srs"),
        Index("ix_srs_version_srs_id", "srs_id"),
    )


class TestCase(db.Model, TimestampMixin, SoftDeleteMixin):
    """LLM-generated test case linked to an SRSVersion."""
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    srs_version_id: Mapped[int] = mapped_column(
        db.ForeignKey("srs_versions.id", ondelete="CASCADE"), nullable=False
    )
    requirement_id: Mapped[str] = mapped_column(db.String(128), nullable=False)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text)
    priority: Mapped[Optional[str]] = mapped_column(db.String(32))
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="generated")  # generated|approved|rejected
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(db.JSON, "sqlite"), nullable=True
    )

    srs_version: Mapped[SRSVersion] = relationship("SRSVersion", back_populates="test_cases")
    scripts: Mapped[list["TestScript"]] = relationship(
        "TestScript", back_populates="test_case", cascade="all, delete-orphan", lazy="selectin"
    )
    results: Mapped[list["TestResult"]] = relationship(
        "TestResult", back_populates="test_case", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_testcase_reqid", "requirement_id"),
        Index("ix_testcase_status", "status"),
    )


class TestScript(db.Model, TimestampMixin, SoftDeleteMixin):
    """Generated pytest script content for a TestCase."""
    __tablename__ = "test_scripts"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    test_case_id: Mapped[int] = mapped_column(db.ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(db.String(32), nullable=False, default="python")
    framework: Mapped[str] = mapped_column(db.String(64), nullable=False, default="pytest-playwright")
    filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    code: Mapped[str] = mapped_column(db.Text, nullable=False)
    last_generated_by: Mapped[Optional[str]] = mapped_column(db.String(128))
    gen_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(db.JSON, "sqlite"), nullable=True
    )

    test_case: Mapped[TestCase] = relationship("TestCase", back_populates="scripts")
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact", back_populates="script", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_testscript_filename", "filename"),
    )


class TestRun(db.Model, TimestampMixin, SoftDeleteMixin):
    """A single execution run which may include many TestResults (multiple cases)."""
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    triggered_by: Mapped[Optional[str]] = mapped_column(db.String(128))
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="queued")  # queued|running|completed|failed
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime)
    run_params: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(db.JSON, "sqlite"), nullable=True
    )

    results: Mapped[list["TestResult"]] = relationship(
        "TestResult", back_populates="test_run", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_testrun_status", "status"),
    )


class TestResult(db.Model, TimestampMixin, SoftDeleteMixin):
    """Result of executing a TestCase as part of a TestRun."""
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    test_run_id: Mapped[int] = mapped_column(db.ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    test_case_id: Mapped[int] = mapped_column(db.ForeignKey("test_cases.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(db.String(16), nullable=False, default="pending")  # passed|failed|skipped|pending
    duration_seconds: Mapped[Optional[float]] = mapped_column(db.Float)
    error_message: Mapped[Optional[str]] = mapped_column(db.Text)
    logs_path: Mapped[Optional[str]] = mapped_column(db.String(1024))
    screenshots_path: Mapped[Optional[str]] = mapped_column(db.String(1024))
    extra: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(db.JSON, "sqlite"), nullable=True
    )

    test_run: Mapped[TestRun] = relationship("TestRun", back_populates="results")
    test_case: Mapped[TestCase] = relationship("TestCase", back_populates="results")

    __table_args__ = (
        Index("ix_testresult_status", "status"),
    )


class Artifact(db.Model, TimestampMixin, SoftDeleteMixin):
    """Generic artifact storage reference (scripts, logs, reports, etc.)."""
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    script_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("test_scripts.id", ondelete="SET NULL"))
    test_run_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("test_runs.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(db.String(64), nullable=False)  # e.g., "script", "log", "report", "screenshot"
    filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(db.String(1024), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(db.String(256))
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(db.JSON, "sqlite"), nullable=True
    )

    script: Mapped[Optional[TestScript]] = relationship("TestScript", back_populates="artifacts")
    test_run: Mapped[Optional[TestRun]] = relationship("TestRun")

    __table_args__ = (
        Index("ix_artifact_kind", "kind"),
    )
