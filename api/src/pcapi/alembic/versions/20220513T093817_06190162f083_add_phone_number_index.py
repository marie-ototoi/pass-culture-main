"""add_phone_number_index
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "06190162f083"
down_revision = "beaefcf60bc9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("COMMIT")
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS "ix_user_phoneNumber" ON "user" ("phoneNumber")
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_phoneNumber"), table_name="user")
