"""Add meta to dataset"""

# revision identifiers, used by Alembic.
revision = 'a1343ebd31c7'
down_revision = '186247cd152e'

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column(
        'dataset',
        sa.Column(
            'meta',
            postgresql.JSONB(),
            nullable=True
        )
    )
    op.execute('''
        UPDATE "dataset" SET
            meta = jsonb_set(coalesce(meta, '{}'), '{organization_id}', to_jsonb(organization_id))
        WHERE
            organization_id IS NOT NULL
    ''')
    op.drop_column('dataset', 'organization_id')


def downgrade():
    op.add_column('dataset', sa.Column('organization_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.execute('''
        UPDATE "dataset" SET
            organization_id = (meta->>'organization_id')::uuid
        WHERE
            meta->>'organization_id' IS NOT NULL
    ''')
    op.drop_column('dataset', 'meta')
