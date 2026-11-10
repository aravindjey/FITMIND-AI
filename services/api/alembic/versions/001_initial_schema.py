"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-24 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'athlete_profiles',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('sex', sa.String(length=20), nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=False),
        sa.Column('current_weight_kg', sa.Float(), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('training_experience_years', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('activity_level', sa.String(length=30), nullable=False),
        sa.Column('occupation_type', sa.String(length=100), nullable=True),
        sa.Column('sport_name', sa.String(length=100), nullable=True),
        sa.Column('sport_position', sa.String(length=50), nullable=True),
        sa.Column('training_preferences', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_athlete_profiles_user_id'), 'athlete_profiles', ['user_id'], unique=True)

    op.create_table(
        'goals',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('primary_goal', sa.String(length=50), nullable=False),
        sa.Column('target_weight_kg', sa.Float(), nullable=True),
        sa.Column('target_date', sa.String(length=20), nullable=True),
        sa.Column('sport_name', sa.String(length=100), nullable=True),
        sa.Column('sport_position', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_athlete_profile_id'), 'goals', ['athlete_profile_id'], unique=False)

    op.create_table(
        'nutrition_profiles',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('bmr_kcal', sa.Integer(), nullable=False),
        sa.Column('tdee_kcal', sa.Integer(), nullable=False),
        sa.Column('target_calories', sa.Integer(), nullable=False),
        sa.Column('protein_grams', sa.Integer(), nullable=False),
        sa.Column('carbs_grams', sa.Integer(), nullable=False),
        sa.Column('fat_grams', sa.Integer(), nullable=False),
        sa.Column('weekly_food_budget_amount', sa.Float(), nullable=True),
        sa.Column('currency_code', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('meals_per_day', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('athlete_profile_id')
    )
    op.create_index(op.f('ix_nutrition_profiles_athlete_profile_id'), 'nutrition_profiles', ['athlete_profile_id'], unique=True)

    op.create_table(
        'check_ins',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('check_in_date', sa.Date(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('energy_score', sa.Integer(), nullable=True),
        sa.Column('sleep_hours', sa.Float(), nullable=True),
        sa.Column('sleep_quality_score', sa.Integer(), nullable=True),
        sa.Column('stress_score', sa.Integer(), nullable=True),
        sa.Column('soreness_score', sa.Integer(), nullable=True),
        sa.Column('hydration_liters', sa.Float(), nullable=True),
        sa.Column('nutrition_adherence_percent', sa.Integer(), nullable=True),
        sa.Column('workout_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('athlete_profile_id', 'check_in_date', name='uq_athlete_check_in_date')
    )
    op.create_index(op.f('ix_check_ins_athlete_profile_id'), 'check_ins', ['athlete_profile_id'], unique=False)

    op.create_table(
        'agent_audit_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('agent_name', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('input_snapshot', sa.JSON(), nullable=False),
        sa.Column('output_snapshot', sa.JSON(), nullable=False),
        sa.Column('validation_passed', sa.Boolean(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('error_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_audit_logs_user_id'), 'agent_audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('agent_audit_logs')
    op.drop_table('check_ins')
    op.drop_table('nutrition_profiles')
    op.drop_table('goals')
    op.drop_table('athlete_profiles')
    op.drop_table('users')
