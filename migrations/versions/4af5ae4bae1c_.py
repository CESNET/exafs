"""empty message

Revision ID: 4af5ae4bae1c
Revises: 67bb6c1b3898
Create Date: 2024-03-27 18:19:35.721215

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4af5ae4bae1c'
down_revision = '67bb6c1b3898'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.add_column(sa.Column('comment', sa.String(length=255), nullable=True))

    with op.batch_alter_table('machine_api_key', schema=None) as batch_op:
        batch_op.add_column(sa.Column('readonly', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('machine_api_key', schema=None) as batch_op:
        batch_op.drop_column('readonly')

    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.drop_column('comment')

    # ### end Alembic commands ###