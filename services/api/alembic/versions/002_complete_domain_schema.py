"""complete_domain_schema

Revision ID: 002_complete_domain_schema
Revises: 001_initial_schema
Create Date: 2026-11-10 07:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

revision: str = '002_complete_domain_schema'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'nutrition_profiles',
        sa.Column('dietary_type', sa.String(length=50), nullable=False, server_default='omnivore')
    )

    op.create_table(
        'food_preferences',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('nutrition_profile_id', GUID(), nullable=False),
        sa.Column('food_name', sa.String(length=150), nullable=False),
        sa.Column('preference_type', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['nutrition_profile_id'], ['nutrition_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_food_preferences_nutrition_profile_id'), 'food_preferences', ['nutrition_profile_id'], unique=False)

    op.create_table(
        'food_items',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('preparation_state', sa.String(length=30), nullable=False, server_default='cooked'),
        sa.Column('serving_unit', sa.String(length=50), nullable=False, server_default='100g'),
        sa.Column('serving_grams', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('calories_per_100g', sa.Float(), nullable=False),
        sa.Column('protein_per_100g', sa.Float(), nullable=False),
        sa.Column('carbs_per_100g', sa.Float(), nullable=False),
        sa.Column('fat_per_100g', sa.Float(), nullable=False),
        sa.Column('fiber_per_100g', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('estimated_cost_inr_per_100g', sa.Float(), nullable=False, server_default='15.0'),
        sa.Column('is_vegetarian', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_vegan', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_indian_staple', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_food_items_name'), 'food_items', ['name'], unique=True)

    op.create_table(
        'nutrition_plans',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('nutrition_profile_id', GUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('daily_calories', sa.Integer(), nullable=False),
        sa.Column('protein_grams', sa.Integer(), nullable=False),
        sa.Column('carbs_grams', sa.Integer(), nullable=False),
        sa.Column('fat_grams', sa.Integer(), nullable=False),
        sa.Column('estimated_daily_cost_inr', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('calculation_assumptions', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_fallback', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['nutrition_profile_id'], ['nutrition_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nutrition_plans_nutrition_profile_id'), 'nutrition_plans', ['nutrition_profile_id'], unique=False)

    op.create_table(
        'meals',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('nutrition_plan_id', GUID(), nullable=False),
        sa.Column('meal_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('time_of_day', sa.String(length=30), nullable=True),
        sa.Column('target_calories', sa.Integer(), nullable=False),
        sa.Column('protein_g', sa.Integer(), nullable=False),
        sa.Column('carbs_g', sa.Integer(), nullable=False),
        sa.Column('fat_g', sa.Integer(), nullable=False),
        sa.Column('estimated_cost_inr', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('recipe_instructions', sa.Text(), nullable=True),
        sa.Column('ingredients', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['nutrition_plan_id'], ['nutrition_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meals_nutrition_plan_id'), 'meals', ['nutrition_plan_id'], unique=False)

    op.create_table(
        'food_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('food_item_id', GUID(), nullable=True),
        sa.Column('log_date', sa.Date(), nullable=False),
        sa.Column('meal_type', sa.String(length=30), nullable=False, server_default='lunch'),
        sa.Column('food_name', sa.String(length=150), nullable=False),
        sa.Column('preparation_state', sa.String(length=30), nullable=False, server_default='cooked'),
        sa.Column('quantity_grams', sa.Float(), nullable=False),
        sa.Column('calories', sa.Float(), nullable=False),
        sa.Column('protein_g', sa.Float(), nullable=False),
        sa.Column('carbs_g', sa.Float(), nullable=False),
        sa.Column('fat_g', sa.Float(), nullable=False),
        sa.Column('cost_inr', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['food_item_id'], ['food_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_food_logs_athlete_profile_id'), 'food_logs', ['athlete_profile_id'], unique=False)
    op.create_index(op.f('ix_food_logs_log_date'), 'food_logs', ['log_date'], unique=False)

    op.create_table(
        'exercises',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('primary_muscle_group', sa.String(length=50), nullable=False),
        sa.Column('secondary_muscles', sa.JSON(), nullable=False),
        sa.Column('equipment_required', sa.String(length=50), nullable=False),
        sa.Column('movement_pattern', sa.String(length=50), nullable=False),
        sa.Column('difficulty_level', sa.String(length=30), nullable=False, server_default='intermediate'),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_exercises_name'), 'exercises', ['name'], unique=True)
    op.create_index(op.f('ix_exercises_primary_muscle_group'), 'exercises', ['primary_muscle_group'], unique=False)

    op.create_table(
        'workout_plans',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('training_split', sa.String(length=50), nullable=False, server_default='upper_lower'),
        sa.Column('duration_weeks', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('days_per_week', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('generated_by_agent', sa.String(length=50), nullable=False, server_default='TrainingAgent'),
        sa.Column('is_fallback', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_plans_athlete_profile_id'), 'workout_plans', ['athlete_profile_id'], unique=False)

    op.create_table(
        'workout_days',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('workout_plan_id', GUID(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('target_focus', sa.String(length=100), nullable=False),
        sa.Column('scheduled_weekday', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workout_plan_id'], ['workout_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_days_workout_plan_id'), 'workout_days', ['workout_plan_id'], unique=False)

    op.create_table(
        'workout_exercises',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('workout_day_id', GUID(), nullable=False),
        sa.Column('exercise_id', GUID(), nullable=False),
        sa.Column('exercise_name', sa.String(length=150), nullable=False),
        sa.Column('order_in_workout', sa.Integer(), nullable=False),
        sa.Column('target_sets', sa.Integer(), nullable=False),
        sa.Column('target_rep_range_min', sa.Integer(), nullable=False),
        sa.Column('target_rep_range_max', sa.Integer(), nullable=False),
        sa.Column('prescribed_weight_kg', sa.Float(), nullable=True),
        sa.Column('target_rpe', sa.Float(), nullable=True),
        sa.Column('rest_seconds', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('tempo', sa.String(length=20), nullable=True),
        sa.Column('progression_rule', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['workout_day_id'], ['workout_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_exercises_workout_day_id'), 'workout_exercises', ['workout_day_id'], unique=False)

    op.create_table(
        'workout_sessions',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('workout_day_id', GUID(), nullable=True),
        sa.Column('workout_name', sa.String(length=150), nullable=False, server_default='Training Session'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_rpe', sa.Float(), nullable=True),
        sa.Column('total_volume_kg', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workout_day_id'], ['workout_days.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_sessions_athlete_profile_id'), 'workout_sessions', ['athlete_profile_id'], unique=False)

    op.create_table(
        'set_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('workout_session_id', GUID(), nullable=False),
        sa.Column('workout_exercise_id', GUID(), nullable=True),
        sa.Column('exercise_id', GUID(), nullable=False),
        sa.Column('exercise_name', sa.String(length=150), nullable=False),
        sa.Column('set_number', sa.Integer(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('reps_completed', sa.Integer(), nullable=False),
        sa.Column('actual_rpe', sa.Float(), nullable=True),
        sa.Column('estimated_1rm_kg', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_warmup', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_pr', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['workout_exercise_id'], ['workout_exercises.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workout_session_id'], ['workout_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_set_logs_workout_session_id'), 'set_logs', ['workout_session_id'], unique=False)

    op.create_table(
        'personal_records',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('exercise_id', GUID(), nullable=False),
        sa.Column('exercise_name', sa.String(length=150), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('reps', sa.Integer(), nullable=False),
        sa.Column('estimated_1rm_kg', sa.Float(), nullable=False),
        sa.Column('achieved_at', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personal_records_athlete_profile_id'), 'personal_records', ['athlete_profile_id'], unique=False)

    op.create_table(
        'body_measurements',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('recorded_at', sa.Date(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('waist_cm', sa.Float(), nullable=True),
        sa.Column('chest_cm', sa.Float(), nullable=True),
        sa.Column('hips_cm', sa.Float(), nullable=True),
        sa.Column('shoulders_cm', sa.Float(), nullable=True),
        sa.Column('bicep_left_cm', sa.Float(), nullable=True),
        sa.Column('bicep_right_cm', sa.Float(), nullable=True),
        sa.Column('thigh_left_cm', sa.Float(), nullable=True),
        sa.Column('thigh_right_cm', sa.Float(), nullable=True),
        sa.Column('calf_cm', sa.Float(), nullable=True),
        sa.Column('neck_cm', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_body_measurements_athlete_profile_id'), 'body_measurements', ['athlete_profile_id'], unique=False)
    op.create_index(op.f('ix_body_measurements_recorded_at'), 'body_measurements', ['recorded_at'], unique=False)

    op.create_table(
        'progress_photos',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('athlete_profile_id', GUID(), nullable=False),
        sa.Column('taken_at', sa.Date(), nullable=False),
        sa.Column('photo_type', sa.String(length=30), nullable=False, server_default='front'),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=50), nullable=False, server_default='image/jpeg'),
        sa.Column('file_size_bytes', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('weight_at_capture_kg', sa.Float(), nullable=True),
        sa.Column('analysis_results', sa.JSON(), nullable=True),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('is_fallback', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['athlete_profile_id'], ['athlete_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_progress_photos_athlete_profile_id'), 'progress_photos', ['athlete_profile_id'], unique=False)
    op.create_index(op.f('ix_progress_photos_taken_at'), 'progress_photos', ['taken_at'], unique=False)

    op.create_table(
        'notifications',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False, server_default='workout'),
        sa.Column('scheduled_time', sa.String(length=20), nullable=False),
        sa.Column('days_of_week', sa.JSON(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('progress_photos')
    op.drop_table('body_measurements')
    op.drop_table('personal_records')
    op.drop_table('set_logs')
    op.drop_table('workout_sessions')
    op.drop_table('workout_exercises')
    op.drop_table('workout_days')
    op.drop_table('workout_plans')
    op.drop_table('exercises')
    op.drop_table('food_logs')
    op.drop_table('meals')
    op.drop_table('nutrition_plans')
    op.drop_table('food_items')
    op.drop_table('food_preferences')
    op.drop_column('nutrition_profiles', 'dietary_type')
