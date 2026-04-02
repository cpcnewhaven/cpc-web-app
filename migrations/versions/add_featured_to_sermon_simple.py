"""Add featured column to Sermon

Revision ID: add_featured_simple
Revises: eb0dfd014d14
Create Date: 2026-04-02 12:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_featured_simple'
down_revision = 'eb0dfd014d14'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sermons', sa.Column('featured', sa.Boolean(), nullable=True, server_default='false'))


def downgrade():
    op.drop_column('sermons', 'featured')
