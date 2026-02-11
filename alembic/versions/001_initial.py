"""Initial migration - create requests table.

Revision ID: 001_initial
Revises: 
Create Date: 2024-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("user_comment", sa.Text(), nullable=True),
        sa.Column("admin_comment", sa.Text(), nullable=True),
        sa.Column("eta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_message_id", sa.BigInteger(), nullable=True),
        sa.Column("admin_message_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_requests_status"), "requests", ["status"], unique=False)
    op.create_index(op.f("ix_requests_user_id"), "requests", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_requests_user_id"), table_name="requests")
    op.drop_index(op.f("ix_requests_status"), table_name="requests")
    op.drop_table("requests")
