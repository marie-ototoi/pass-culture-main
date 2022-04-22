"""delete-email-table
"""
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec56470e02d7'
down_revision = 'beaefcf60bc9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("email")
    op.execute("DROP TYPE emailstatus")


def downgrade() -> None:
    op.execute("CREATE TYPE emailstatus AS ENUM('SENT','ERROR')")
    op.create_table(
        "email",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("datetime", sa.DateTime(), nullable=False),
    )
