"""Add order"""

# revision identifiers, used by Alembic.
revision = 'aca3b384e03a'
down_revision = 'd616b0a80feb'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('problem_label', sa.Column('order_index', sa.Integer(), nullable=True))
    op.execute('''
        UPDATE problem_label SET order_index = 0
    ''')
    op.alter_column('problem_label', 'order_index', nullable=False)

def downgrade():
    op.drop_column('problem_label', 'order_index')
