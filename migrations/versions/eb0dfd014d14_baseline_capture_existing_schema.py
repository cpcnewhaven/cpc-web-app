"""baseline: capture existing schema

Revision ID: eb0dfd014d14
Revises: 
Create Date: 2026-02-10 13:14:12.021900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb0dfd014d14'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Baseline migration — schema already exists in production.
    # This revision exists only to establish the Alembic version marker.
    pass


def downgrade():
    # Baseline migration — nothing to reverse.
    pass
