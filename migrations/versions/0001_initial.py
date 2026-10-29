"""Начальная миграция: пользователи, поездки, пункты плана.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("username"))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("trips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("budget", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("is_completed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("end_date >= start_date", name="ck_trip_dates"))
    op.create_index("ix_trips_owner_id", "trips", ["owner_id"])
    op.create_table("plan_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("day_date", sa.Date(), nullable=False),
        sa.Column("time_text", sa.String(20), nullable=True),
        sa.Column("place", sa.String(200), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("is_done", sa.Boolean(), server_default="0", nullable=False))
    op.create_index("ix_plan_items_trip_id", "plan_items", ["trip_id"])

def downgrade():
    op.drop_index("ix_plan_items_trip_id", table_name="plan_items")
    op.drop_table("plan_items")
    op.drop_index("ix_trips_owner_id", table_name="trips")
    op.drop_table("trips")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
