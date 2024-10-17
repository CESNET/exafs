"""limit for each type of rule, org id as a key for each rule

Revision ID: e25b385bae2c
Revises: 58ac38ced7f6
Create Date: 2024-10-17 16:41:01.116727

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e25b385bae2c'
down_revision = '58ac38ced7f6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('RTBH', schema=None) as batch_op:
        batch_op.add_column(sa.Column('org_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'organization', ['org_id'], ['id'])

    with op.batch_alter_table('flowspec4', schema=None) as batch_op:
        batch_op.add_column(sa.Column('org_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'organization', ['org_id'], ['id'])

    with op.batch_alter_table('flowspec6', schema=None) as batch_op:
        batch_op.add_column(sa.Column('org_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'organization', ['org_id'], ['id'])

    with op.batch_alter_table('log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('org_id', sa.Integer(), nullable=True))

    with op.batch_alter_table('organization', schema=None) as batch_op:
        batch_op.add_column(sa.Column('limit_flowspec4', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('limit_flowspec6', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('limit_rtbh', sa.Integer(), nullable=True))
        batch_op.drop_column('ipv6count')
        batch_op.drop_column('rule_limit')
        batch_op.drop_column('rtbhcount')
        batch_op.drop_column('ipv4count')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('organization', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ipv4count', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('rtbhcount', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('rule_limit', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('ipv6count', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
        batch_op.drop_column('limit_rtbh')
        batch_op.drop_column('limit_flowspec6')
        batch_op.drop_column('limit_flowspec4')

    with op.batch_alter_table('log', schema=None) as batch_op:
        batch_op.drop_column('org_id')

    with op.batch_alter_table('flowspec6', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('org_id')

    with op.batch_alter_table('flowspec4', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('org_id')

    with op.batch_alter_table('RTBH', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('org_id')

    # ### end Alembic commands ###
