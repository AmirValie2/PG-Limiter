"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('owner_username', sa.String(length=255), nullable=True),
        sa.Column('group_ids', sa.JSON(), nullable=True),
        sa.Column('data_limit', sa.Float(), nullable=True),
        sa.Column('used_traffic', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expire_at', sa.DateTime(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_owner_id', 'users', ['owner_id'], unique=False)
    op.create_index('ix_users_status', 'users', ['status'], unique=False)

    # Create user_limits table
    op.create_table(
        'user_limits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('limit', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['username'], ['users.username'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_limits_username', 'user_limits', ['username'], unique=True)

    # Create except_users table
    op.create_table(
        'except_users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_except_users_username', 'except_users', ['username'], unique=True)

    # Create disabled_users table
    op.create_table(
        'disabled_users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('disabled_at', sa.Float(), nullable=False),
        sa.Column('enable_at', sa.Float(), nullable=True),
        sa.Column('original_groups', sa.JSON(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('punishment_step', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['username'], ['users.username'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_disabled_users_username', 'disabled_users', ['username'], unique=True)

    # Create subnet_isp table
    op.create_table(
        'subnet_isp',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subnet', sa.String(length=50), nullable=False),
        sa.Column('isp', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=10), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('asn', sa.String(length=50), nullable=True),
        sa.Column('as_name', sa.String(length=255), nullable=True),
        sa.Column('cached_at', sa.DateTime(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_subnet_isp_subnet', 'subnet_isp', ['subnet'], unique=True)
    op.create_index('ix_subnet_isp_country', 'subnet_isp', ['country'], unique=False)
    op.create_index('ix_subnet_isp_isp', 'subnet_isp', ['isp'], unique=False)

    # Create violation_history table
    op.create_table(
        'violation_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('step_applied', sa.Integer(), nullable=False),
        sa.Column('disable_duration', sa.Integer(), nullable=False),
        sa.Column('enabled_at', sa.Float(), nullable=True),
        sa.Column('ip_count', sa.Integer(), nullable=True),
        sa.Column('ips', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['username'], ['users.username'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_violation_history_username', 'violation_history', ['username'], unique=False)
    op.create_index('ix_violation_history_timestamp', 'violation_history', ['timestamp'], unique=False)

    # Create config table
    op.create_table(
        'config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_config_key', 'config', ['key'], unique=True)

    # Create ip_history table
    op.create_table(
        'ip_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('ip', sa.String(length=45), nullable=False),
        sa.Column('node_name', sa.String(length=255), nullable=True),
        sa.Column('inbound_protocol', sa.String(length=100), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('connection_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ip_history_username_ip', 'ip_history', ['username', 'ip'], unique=False)
    op.create_index('ix_ip_history_last_seen', 'ip_history', ['last_seen'], unique=False)


def downgrade() -> None:
    op.drop_table('ip_history')
    op.drop_table('config')
    op.drop_table('violation_history')
    op.drop_table('subnet_isp')
    op.drop_table('disabled_users')
    op.drop_table('except_users')
    op.drop_table('user_limits')
    op.drop_table('users')
