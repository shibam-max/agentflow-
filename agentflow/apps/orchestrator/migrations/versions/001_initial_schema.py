"""Initial schema — tasks, runs, agent_steps, embeddings

Revision ID: 001
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    op.create_table(
        'tasks',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), server_default='PENDING'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_tasks_user', 'tasks', ['user_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])

    op.create_table(
        'runs',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', UUID, sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('status', sa.String(20), server_default='RUNNING'),
        sa.Column('revision_count', sa.Integer, server_default='0'),
        sa.Column('critic_score', sa.Float),
        sa.Column('final_output', sa.Text),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),
    )
    op.create_index('idx_runs_task', 'runs', ['task_id'])
    op.create_index('idx_runs_status', 'runs', ['status'])

    op.create_table(
        'agent_steps',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', UUID, sa.ForeignKey('runs.id'), nullable=False),
        sa.Column('agent_name', sa.String(50), nullable=False),
        sa.Column('input', JSONB),
        sa.Column('output', sa.Text),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('token_count', sa.Integer),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_steps_run', 'agent_steps', ['run_id'])

    op.execute("""
        CREATE TABLE embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX ON embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade():
    op.drop_table('agent_steps')
    op.drop_table('runs')
    op.drop_table('tasks')
    op.execute("DROP TABLE IF EXISTS embeddings")
