"""empty message

Revision ID: 67bb6c1b3898
Revises: 2bd0e800ab1c
Create Date: 2024-03-27 18:13:10.688958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67bb6c1b3898'
down_revision = '2bd0e800ab1c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('machine_api_key',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('machine', sa.String(length=255), nullable=True),
    sa.Column('key', sa.String(length=255), nullable=True),
    sa.Column('expires', sa.DateTime(), nullable=True),
    sa.Column('comment', sa.String(length=255), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.add_column(sa.Column('readonly', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('expires', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.drop_column('expires')
        batch_op.drop_column('readonly')

    op.drop_table('machine_api_key')
    # ### end Alembic commands ###
