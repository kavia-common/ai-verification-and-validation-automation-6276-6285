"""Initial schema: SRS, SRSVersion, TestCase, TestScript, TestRun, TestResult, Artifact

Revision ID: 0001_initial
Revises: 
Create Date: 2025-12-12 00:00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # srs
    op.create_table(
        "srs",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.String(length=128), nullable=True),
    )
    op.create_index("ix_srs_name", "srs", ["name"], unique=False)

    # srs_versions
    op.create_table(
        "srs_versions",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("srs_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("file_hash", sa.String(length=256), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["srs_id"], ["srs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("srs_id", "version", name="uq_srs_version_per_srs"),
    )
    op.create_index("ix_srs_version_srs_id", "srs_versions", ["srs_id"], unique=False)

    # test_cases
    op.create_table(
        "test_cases",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("srs_version_id", sa.Integer(), nullable=False),
        sa.Column("requirement_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="generated"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["srs_version_id"], ["srs_versions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_testcase_reqid", "test_cases", ["requirement_id"], unique=False)
    op.create_index("ix_testcase_status", "test_cases", ["status"], unique=False)

    # test_scripts
    op.create_table(
        "test_scripts",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("test_case_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False, server_default="python"),
        sa.Column("framework", sa.String(length=64), nullable=False, server_default="pytest-playwright"),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("last_generated_by", sa.String(length=128), nullable=True),
        sa.Column("gen_metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_testscript_filename", "test_scripts", ["filename"], unique=False)

    # test_runs
    op.create_table(
        "test_runs",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("triggered_by", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("run_params", sa.JSON(), nullable=True),
    )
    op.create_index("ix_testrun_status", "test_runs", ["status"], unique=False)

    # test_results
    op.create_table(
        "test_results",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("test_run_id", sa.Integer(), nullable=False),
        sa.Column("test_case_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("logs_path", sa.String(length=1024), nullable=True),
        sa.Column("screenshots_path", sa.String(length=1024), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["test_run_id"], ["test_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_testresult_status", "test_results", ["status"], unique=False)

    # artifacts
    op.create_table(
        "artifacts",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("script_id", sa.Integer(), nullable=True),
        sa.Column("test_run_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("checksum", sa.String(length=256), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["script_id"], ["test_scripts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["test_run_id"], ["test_runs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_artifact_kind", "artifacts", ["kind"], unique=False)


def downgrade():
    op.drop_index("ix_artifact_kind", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("ix_testresult_status", table_name="test_results")
    op.drop_table("test_results")
    op.drop_index("ix_testrun_status", table_name="test_runs")
    op.drop_table("test_runs")
    op.drop_index("ix_testscript_filename", table_name="test_scripts")
    op.drop_table("test_scripts")
    op.drop_index("ix_testcase_status", table_name="test_cases")
    op.drop_index("ix_testcase_reqid", table_name="test_cases")
    op.drop_table("test_cases")
    op.drop_index("ix_srs_version_srs_id", table_name="srs_versions")
    op.drop_table("srs_versions")
    op.drop_index("ix_srs_name", table_name="srs")
    op.drop_table("srs")
