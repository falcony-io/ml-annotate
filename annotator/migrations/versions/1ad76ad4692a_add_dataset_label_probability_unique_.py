"""Add dataset label probability unique constraint"""

# revision identifiers, used by Alembic.
revision = '1ad76ad4692a'
down_revision = '0fd16cdac8ca'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_unique_constraint('uq_dataset_label_probability_data_id_label_id', 'dataset_label_probability', ['data_id', 'label_id'])


def downgrade():
    op.drop_constraint('uq_dataset_label_probability_data_id_label_id', 'dataset_label_probability', type_='unique')
