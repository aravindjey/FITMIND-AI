'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import EmptyState from '@/components/EmptyState';
import {
  User,
  Dumbbell,
  Utensils,
  Calendar,
  Activity,
  Award,
  Flame,
  TrendingUp,
  Bot,
  ClipboardCheck,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

export default function DashboardPage() {
  const [state, setState] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [generatingWorkout, setGeneratingWorkout] = useState(false);
  const [generatingNutrition, setGeneratingNutrition] = useState(false);

  const loadState = () => {
    setLoading(true);
    apiClient
      .getHydratedState()
      .then((data) => setState(data))
      .catch(() => setState(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadState();
  }, []);

  const handleQuickGenerateWorkout = async () => {
    setGeneratingWorkout(true);
    try {
      await apiClient.generateWorkoutPlan();
      loadState();
    } catch {
      // handled on workout page
    } finally {
      setGeneratingWorkout(false);
    }
  };

  const handleQuickGenerateNutrition = async () => {
    setGeneratingNutrition(true);
    try {
      await apiClient.generateNutritionPlan();
      loadState();
    } catch {
      // handled on nutrition page
    } finally {
      setGeneratingNutrition(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-gray-400">
        <span>Loading Authoritative Athlete State...</span>
      </div>
    );
  }

  if (!state || !state.has_profile) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Athlete Overview</h1>
          <p className="text-sm text-gray-400">Your current athletic status and active plans</p>
        </div>

        <EmptyState
          icon={User}
          title="Complete Athlete Onboarding"
          description="You have not completed your athlete assessment yet. Configure your biometrics, goals, equipment, Indian staple foods, and INR food budget to unlock personalized AI coaching."
          actionText="Start Athlete Onboarding"
          actionHref="/onboarding"
        />
      </div>
    );
  }

  const summary = state.athlete_summary || {};
  const targets = state.nutrition_targets || {};
  const weightTrend = state.recent_weight_trend || {};
  const recovery = state.recent_recovery || null;
  const workoutPlan = state.active_workout_plan;
  const nutritionPlan = state.active_nutrition_plan;
  const prs = state.personal_records || [];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">FITMIND AI Command Center</h1>
          <p className="text-sm text-gray-400">
            Intelligent Fitness. Science-Driven Results. • Goal:{' '}
            <span className="text-brand-400 font-medium capitalize">
              {(summary.primary_goal || 'general_fitness').replace('_', ' ')}
            </span>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/check-in"
            className="px-4 py-2 rounded-xl bg-dark-800 border border-gray-700 hover:border-brand-500 text-xs font-semibold text-gray-200 flex items-center gap-2 transition-colors"
          >
            <ClipboardCheck className="w-4 h-4 text-brand-500" />
            <span>Log Daily Check-In</span>
          </Link>
          <Link
            href="/ai-coach"
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-xs font-semibold text-white flex items-center gap-2 transition-colors"
          >
            <Bot className="w-4 h-4" />
            <span>Ask FitMind AI</span>
          </Link>
        </div>
      </div>

      {/* Goal vs Target Weight Conflict Warning */}
      {targets.goal_conflict_warning && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start justify-between gap-4">
          <div>
            <span className="font-bold text-amber-200 block mb-0.5">
              ⚠️ Goal &amp; Target Weight Consistency Warning
            </span>
            <span>{targets.goal_conflict_warning}</span>
          </div>
          <Link
            href="/profile"
            className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 font-semibold whitespace-nowrap self-center"
          >
            Clarify Goal
          </Link>
        </div>
      )}

      {/* Primary Biometrics & Readiness Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Body Weight</span>
            <TrendingUp className="w-4 h-4 text-brand-500" />
          </div>
          <div className="text-2xl font-bold text-white">
            {summary.weight_kg} <span className="text-sm font-normal text-gray-400">kg</span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            7d EMA:{' '}
            <span className="text-gray-200 font-medium">
              {weightTrend.ema_latest_kg || summary.weight_kg} kg
            </span>
            {summary.target_weight_kg ? ` • Target: ${summary.target_weight_kg} kg` : ''}
          </div>
        </div>

        <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Daily Target</span>
            <Flame className="w-4 h-4 text-orange-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {targets.target_calories || '—'} <span className="text-sm font-normal text-gray-400">kcal</span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            P: <span className="text-emerald-400">{targets.protein_grams ?? '—'}g</span> • C:{' '}
            <span className="text-blue-400">{targets.carbs_grams ?? '—'}g</span> • F:{' '}
            <span className="text-amber-400">{targets.fat_grams ?? '—'}g</span>
          </div>
        </div>

        <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Recovery Readiness</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {recovery ? `${recovery.readiness_score}/100` : 'No Check-In'}
          </div>
          <div className="text-xs text-gray-400 mt-1 capitalize">
            {recovery
              ? `${(recovery.status || 'baseline').replace('_', ' ')} (${recovery.intensity_modifier ?? 1.0}x load)`
              : 'Submit check-in to compute readiness'}
          </div>
        </div>

        <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Metabolic Baseline</span>
            <User className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {targets.tdee_kcal || '—'} <span className="text-sm font-normal text-gray-400">TDEE</span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            BMR: {targets.bmr_kcal || '—'} kcal • Exp: {summary.training_experience_years} yrs
          </div>
        </div>
      </div>

      {/* Active Plans Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Active Workout Plan Card */}
        <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500">
                  <Dumbbell className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white">Active Workout Plan</h3>
                  <p className="text-xs text-gray-400">Periodized training program</p>
                </div>
              </div>
              <Link href="/workout" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
                <span>Open Planner</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {workoutPlan ? (
              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800">
                  <div className="font-semibold text-white text-sm">{workoutPlan.name}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    Split:{' '}
                    <span className="text-gray-200 uppercase">
                      {(workoutPlan.training_split || 'upper_lower').replace('_', ' ')}
                    </span>{' '}
                    • {workoutPlan.days_per_week} days/week
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center bg-gray-900/40 border border-gray-800/80 rounded-xl space-y-3">
                <Calendar className="w-8 h-8 text-gray-500 mx-auto" />
                <div className="text-sm font-medium text-white">No Active Workout Plan</div>
                <p className="text-xs text-gray-400">
                  Generate a personalized periodized training split tailored to your equipment and schedule.
                </p>
                <button
                  onClick={handleQuickGenerateWorkout}
                  disabled={generatingWorkout}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl inline-flex items-center gap-2"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{generatingWorkout ? 'Generating Plan...' : 'Generate Workout Plan'}</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Active Nutrition Plan Card */}
        <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500">
                  <Utensils className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white">Active Nutrition Plan</h3>
                  <p className="text-xs text-gray-400">Constraint & INR budget-aware meal plan</p>
                </div>
              </div>
              <Link href="/nutrition" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
                <span>Open Nutrition</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {nutritionPlan ? (
              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800">
                  <div className="font-semibold text-white text-sm">{nutritionPlan.name}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    Target: <span className="text-white font-medium">{nutritionPlan.daily_calories} kcal</span> •{' '}
                    {nutritionPlan.meal_count} meals/day
                  </div>
                  <div className="text-xs text-emerald-400 mt-1.5">
                    Est. Daily Cost: ₹{nutritionPlan.estimated_daily_cost_inr} INR (~₹
                    {Math.round((nutritionPlan.estimated_daily_cost_inr || 0) * 7)}/week)
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center bg-gray-900/40 border border-gray-800/80 rounded-xl space-y-3">
                <Utensils className="w-8 h-8 text-gray-500 mx-auto" />
                <div className="text-sm font-medium text-white">No Active Nutrition Plan</div>
                <p className="text-xs text-gray-400">
                  Generate an Indian staple-aware meal plan respecting your dietary type, allergies, and ₹ INR budget.
                </p>
                <button
                  onClick={handleQuickGenerateNutrition}
                  disabled={generatingNutrition}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl inline-flex items-center gap-2"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{generatingNutrition ? 'Generating Meals...' : 'Generate Nutrition Plan'}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Personal Records & Recent Activity */}
      <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white">Personal Records (Estimated 1RM)</h3>
              <p className="text-xs text-gray-400">Automatically tracked from logged workout sets</p>
            </div>
          </div>
          <Link href="/progress" className="text-xs text-brand-400 hover:text-brand-300">
            View Full Analytics →
          </Link>
        </div>

        {prs.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {prs.map((pr: any, idx: number) => (
              <div key={idx} className="p-3.5 rounded-xl bg-gray-900 border border-gray-800">
                <div className="text-xs text-gray-400 truncate">{pr.exercise_name}</div>
                <div className="text-lg font-bold text-white mt-0.5">{pr.estimated_1rm_kg} kg</div>
                <div className="text-[11px] text-gray-500">
                  Best set: {pr.weight_kg} kg × {pr.reps} reps
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-gray-400 py-4">
            No personal records logged yet. Log your first workout session in the{' '}
            <Link href="/workout" className="text-brand-400 underline">
              Workout Logger
            </Link>{' '}
            to compute Epley 1RM milestones.
          </div>
        )}
      </div>
    </div>
  );
}
