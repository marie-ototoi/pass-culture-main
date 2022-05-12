"""add_educational_domains_table
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d015da71632f"
down_revision = "3c19643259f9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "educational_domain",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "collective_offer_domain",
        sa.Column("collectiveOfferId", sa.BigInteger(), nullable=False),
        sa.Column("educationalDomainId", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collectiveOfferId"],
            ["collective_offer.id"],
        ),
        sa.ForeignKeyConstraint(
            ["educationalDomainId"],
            ["educational_domain.id"],
        ),
        sa.PrimaryKeyConstraint("collectiveOfferId", "educationalDomainId"),
        sa.UniqueConstraint(
            "collectiveOfferId", "educationalDomainId", name="unique_collective_offer_domain_association"
        ),
    )
    op.create_index(
        op.f("ix_collective_offer_domain_collectiveOfferId"),
        "collective_offer_domain",
        ["collectiveOfferId"],
        unique=False,
    )
    op.create_index(
        op.f("ix_collective_offer_domain_educationalDomainId"),
        "collective_offer_domain",
        ["educationalDomainId"],
        unique=False,
    )
    op.create_table(
        "collective_offer_template_domain",
        sa.Column("collectiveOfferTemplateId", sa.BigInteger(), nullable=False),
        sa.Column("educationalDomainId", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collectiveOfferTemplateId"],
            ["collective_offer_template.id"],
        ),
        sa.ForeignKeyConstraint(
            ["educationalDomainId"],
            ["educational_domain.id"],
        ),
        sa.PrimaryKeyConstraint("collectiveOfferTemplateId", "educationalDomainId"),
        sa.UniqueConstraint(
            "collectiveOfferTemplateId",
            "educationalDomainId",
            name="unique_collective_offer_template_domain_association",
        ),
    )
    op.create_index(
        op.f("ix_collective_offer_template_domain_collectiveOfferTemplateId"),
        "collective_offer_template_domain",
        ["collectiveOfferTemplateId"],
        unique=False,
    )
    op.create_index(
        op.f("ix_collective_offer_template_domain_educationalDomainId"),
        "collective_offer_template_domain",
        ["educationalDomainId"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_collective_offer_template_domain_educationalDomainId"), table_name="collective_offer_template_domain"
    )
    op.drop_index(
        op.f("ix_collective_offer_template_domain_collectiveOfferTemplateId"),
        table_name="collective_offer_template_domain",
    )
    op.drop_table("collective_offer_template_domain")
    op.drop_index(op.f("ix_collective_offer_domain_educationalDomainId"), table_name="collective_offer_domain")
    op.drop_index(op.f("ix_collective_offer_domain_collectiveOfferId"), table_name="collective_offer_domain")
    op.drop_table("collective_offer_domain")
    op.drop_table("educational_domain")
