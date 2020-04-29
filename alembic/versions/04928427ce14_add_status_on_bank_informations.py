"""add_status_on_bank_informations

Revision ID: 04928427ce14
Revises: 176d931e5dbc
Create Date: 2020-04-28 09:58:34.287483

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04928427ce14'
down_revision = '176d931e5dbc'
branch_labels = None
depends_on = None

values = ('ACCEPTED', 'REJECTED', 'DRAFT')
enum = sa.Enum(*values, name='status')


def upgrade():
    op.alter_column('bank_information', 'bic', nullable=True)
    op.alter_column('bank_information', 'iban', nullable=True)

    enum.create(op.get_bind(), checkfirst=False)

    op.add_column('bank_information', sa.Column(
        'status', enum, nullable=True))
    op.execute("UPDATE bank_information SET status = 'ACCEPTED'")
    op.alter_column('bank_information', 'status', nullable=False)


def downgrade():
    op.alter_column('bank_information', 'bic', nullable=False)
    op.alter_column('bank_information', 'iban', nullable=False)

    op.drop_column('bank_information', 'status')
    enum.drop(op.get_bind(), checkfirst=False)
