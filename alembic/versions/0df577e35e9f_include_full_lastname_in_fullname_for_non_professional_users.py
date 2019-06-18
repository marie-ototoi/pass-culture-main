"""include_full_lastname_in_fullname_for_non_professional_users

Revision ID: 0df577e35e9f
Revises: 4127e9899829
Create Date: 2019-06-13 14:38:46.600200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0df577e35e9f'
down_revision = '4127e9899829'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE "user" 
        SET "publicName" = concat("firstName", ' ', "lastName")
        WHERE "dateOfBirth" IS NOT NULL;
    """)
    pass


def downgrade():
    op.execute("""
        UPDATE "user"
        SET "publicName" = concat("firstName", ' ', upper(substring("lastName" from 1 for 1)), '.')
        WHERE "dateOfBirth" IS NOT NULL;
    """)
    pass
