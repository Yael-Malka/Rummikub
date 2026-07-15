"""Add boards, games and turns tables.

Revision ID: c7e4a19b2f80
Revises: 565eed23caf7
Create Date: 2026-03-18 14:22:11.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c7e4a19b2f80"
down_revision: Union[str, Sequence[str], None] = "565eed23caf7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create boards, games, and turns tables."""
    op.create_table(
        "boards",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column("hand_image_path", sa.Text(), nullable=True),
        sa.Column("classification_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("form_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("hand_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("solution", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_discarded", sa.Boolean(), nullable=True),
        sa.Column("in_progress", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="processing", nullable=False),
        sa.Column("failure_code", sa.String(length=32), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_boards_id"), "boards", ["id"], unique=False)
    op.create_index(op.f("ix_boards_in_progress"), "boards", ["in_progress"], unique=False)
    op.create_index(op.f("ix_boards_status"), "boards", ["status"], unique=False)
    op.create_index(op.f("ix_boards_user_id"), "boards", ["user_id"], unique=False)

    op.create_table(
        "games",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_shared", sa.Boolean(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_games_user_id"), "games", ["user_id"], unique=False)

    op.create_table(
        "turns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("board_image_url", sa.Text(), nullable=True),
        sa.Column("hand_image_url", sa.Text(), nullable=True),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_first_drop", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_turns_game_id"), "turns", ["game_id"], unique=False)


def downgrade() -> None:
    """Drop boards, games, and turns tables."""
    op.drop_index(op.f("ix_turns_game_id"), table_name="turns")
    op.drop_table("turns")
    op.drop_index(op.f("ix_games_user_id"), table_name="games")
    op.drop_table("games")
    op.drop_index(op.f("ix_boards_user_id"), table_name="boards")
    op.drop_index(op.f("ix_boards_status"), table_name="boards")
    op.drop_index(op.f("ix_boards_in_progress"), table_name="boards")
    op.drop_index(op.f("ix_boards_id"), table_name="boards")
    op.drop_table("boards")