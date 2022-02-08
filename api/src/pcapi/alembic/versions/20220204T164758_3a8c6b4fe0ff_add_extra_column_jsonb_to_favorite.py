"""add extra column (JSONB) to favorite
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "3a8c6b4fe0ff"
down_revision = "28a13156d2d8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("favorite", sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column("favorite", "extra")
