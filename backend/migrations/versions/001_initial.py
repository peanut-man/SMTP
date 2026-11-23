"""Initial database schema migration

Revision ID: 001_initial
Revises: 
Create Date: 2026-11-23 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'USER', name='user_role'), nullable=False, server_default='USER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. smtp_accounts
    op.create_table(
        'smtp_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_name', sa.String(length=128), nullable=False),
        sa.Column('smtp_host', sa.String(length=255), nullable=False),
        sa.Column('smtp_port', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('encrypted_password', sa.Text(), nullable=False),
        sa.Column('security_mode', sa.Enum('STARTTLS', 'SSL_TLS', 'PLAIN', name='security_mode'), nullable=False, server_default='STARTTLS'),
        sa.Column('sender_email', sa.String(length=255), nullable=False),
        sa.Column('sender_name', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('connection_timeout', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_test_status', sa.Enum('SUCCESS', 'FAILED', 'UNTESTED', name='test_status'), nullable=False, server_default='UNTESTED'),
        sa.Column('last_test_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_smtp_accounts_user_id', 'smtp_accounts', ['user_id'])

    # 3. email_templates
    op.create_table(
        'email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subject', sa.String(length=998), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_email_templates_user_id', 'email_templates', ['user_id'])

    # 4. email_jobs
    op.create_table(
        'email_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('smtp_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('smtp_accounts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('subject', sa.String(length=998), nullable=False),
        sa.Column('sender_email', sa.String(length=255), nullable=False),
        sa.Column('sender_name', sa.String(length=255), nullable=True),
        sa.Column('reply_to', sa.String(length=255), nullable=True),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('text_body', sa.Text(), nullable=True),
        sa.Column('recipient_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('message_type', sa.Enum('DIRECT', 'TEMPLATE', 'TEST', name='message_type'), nullable=False, server_default='DIRECT'),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_templates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('attachments_meta', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'ACCEPTED', 'FAILED', 'RETRYING', 'CANCELLED', name='job_status'), nullable=False, server_default='PENDING'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_email_jobs_user_id', 'email_jobs', ['user_id'])
    op.create_index('ix_email_jobs_smtp_account_id', 'email_jobs', ['smtp_account_id'])
    op.create_index('ix_email_jobs_status', 'email_jobs', ['status'])
    op.create_index('ix_email_jobs_created_at', 'email_jobs', ['created_at'])

    # 5. email_recipients
    op.create_table(
        'email_recipients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('recipient_type', sa.Enum('TO', 'CC', 'BCC', name='recipient_type'), nullable=False, server_default='TO'),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'FAILED', name='recipient_status'), nullable=False, server_default='PENDING'),
        sa.Column('smtp_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_email_recipients_email_job_id', 'email_recipients', ['email_job_id'])

    # 6. email_attempts
    op.create_table(
        'email_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('smtp_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('smtp_accounts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('SUCCESS', 'FAILED', 'TIMEOUT', name='attempt_status'), nullable=False),
        sa.Column('smtp_response_code', sa.Integer(), nullable=True),
        sa.Column('smtp_response_message', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_email_attempts_email_job_id', 'email_attempts', ['email_job_id'])

    # 7. contacts
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('group_name', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_contacts_user_id', 'contacts', ['user_id'])
    op.create_index('ix_contacts_email', 'contacts', ['email'])
    op.create_index('ix_contacts_group_name', 'contacts', ['group_name'])


def downgrade() -> None:
    op.drop_table('contacts')
    op.drop_table('email_attempts')
    op.drop_table('email_recipients')
    op.drop_table('email_jobs')
    op.drop_table('email_templates')
    op.drop_table('smtp_accounts')
    op.drop_table('users')
