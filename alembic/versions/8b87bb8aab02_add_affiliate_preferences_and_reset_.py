"""Add affiliate preferences and reset tracking

Revision ID: XXXXX
Revises: YYYYY
Create Date: 2025-11-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'XXXXX'  # Déjalo como está
down_revision = 'YYYYY'  # Déjalo como está
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columnas a api_keys
    op.add_column('api_keys', 
        sa.Column('affiliate_preference', sa.String(20), 
                  server_default='hybrid90_url', nullable=False)
    )
    op.add_column('api_keys',
        sa.Column('last_reset_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Crear índice para búsquedas por tier
    op.create_index('idx_api_keys_tier', 'api_keys', ['tier'])


def downgrade():
    # Revertir cambios
    op.drop_index('idx_api_keys_tier', table_name='api_keys')
    op.drop_column('api_keys', 'last_reset_at')
    op.drop_column('api_keys', 'affiliate_preference')