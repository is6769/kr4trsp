from alembic import op
import sqlalchemy as sa


revision = '002_add_description'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column('description', sa.String(length=1000), nullable=False, server_default='No description')
    )


def downgrade() -> None:
    op.drop_column('products', 'description')
