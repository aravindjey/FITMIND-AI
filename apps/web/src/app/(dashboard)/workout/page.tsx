'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import {
  Dumbbell,
  Sparkles,
  CheckCircle,
  AlertCircle,
  Plus,
  Trash2,
  Award,
  TrendingUp,
  History,
} from 'lucide-react';

export default function WorkoutPage() {
  const [plan, setPlan] = useState<any | null>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [prs, setPrs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [logging, setLogging] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedDayIdx, setSelectedDayIdx] = useState(0);
  const [lastSessionResult, setLastSessionResult] = useState<any | null>(null);

  const [workoutName, setWorkoutName] = useState('Upper Body Hypertrophy');
  const [sessionRpe, setSessionRpe] = useState(8);
  const [sessionNotes, setSessionNotes] = useState('');
  const [sets, setSets] = useState<
    Array<{
      exercise_name: string;
      set_number: number;
      weight_kg: number;
      reps_completed: number;
      actual_rpe: number;
    }>
  >([
    { exercise_name: 'Barbell Bench Press', set_number: 1, weight_kg: 60, reps_completed: 10, actual_rpe: 8 },
    { exercise_name: 'Barbell Bench Press', set_number: 2, weight_kg: 60, reps_completed: 10, actual_rpe: 8.5 },
    { exercise_name: 'Barbell Bent-Over Row', set_number: 1, weight_kg: 55, reps_completed: 10, actual_rpe: 8 },
  ]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [activePlanRes, sessionsRes, prsRes] = await Promise.all([
        apiClient.getActiveWorkoutPlan(),
        apiClient.listWorkoutSessions(),
        apiClient.listPersonalRecords(),
      ]);
      if (activePlanRes?.has_active_plan) {
        setPlan(activePlanRes.plan);
        if (activePlanRes.plan.days?.length > 0) {
          const day = activePlanRes.plan.days[0];
          setWorkoutName(day.day_name);
          if (day.exercises?.length > 0) {
            setSets(
              day.exercises.slice(0, 3).map((ex: any, i: number) => ({
                exercise_name: ex.exercise_name,
                set_number: 1,
                weight_kg: 40 + i * 10,
                reps_completed: ex.rep_Max || ex.rep_max || 10,
                actual_rpe: ex.target_rpe || 8,
              }))
            );
          }
        }
      }
      setSessions(sessionsRes || []);
      setPrs(prsRes || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load training data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGeneratePlan = async () => {
    setGenerating(true);
    setError(null);
    setMessage(null);
    try {
      const res = await apiClient.generateWorkoutPlan();
      setMessage(
        `Generated workout plan "${res.plan.name}" (${res.is_fallback ? 'Deterministic Engine Fallback' : 'Live AI Provider'})`
      );
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to generate workout plan. Complete onboarding first.');
    } finally {
      setGenerating(false);
    }
  };

  const handleAddSet = () => {
    const last = sets[sets.length - 1];
    setSets([
      ...sets,
      {
        exercise_name: last ? last.exercise_name : 'Barbell Back Squat',
        set_number: last ? last.set_number + 1 : 1,
        weight_kg: last ? last.weight_kg : 60,
        reps_completed: last ? last.reps_completed : 8,
        actual_rpe: 8,
      },
    ]);
  };

  const handleRemoveSet = (idx: number) => {
    setSets(sets.filter((_, i) => i !== idx));
  };

  const handleLogSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (sets.length === 0) return;
    setLogging(true);
    setError(null);
    setMessage(null);
    try {
      const res = await apiClient.logWorkoutSession({
        workout_name: workoutName,
        session_rpe: sessionRpe,
        user_notes: sessionNotes,
        sets,
      });
      setLastSessionResult(res);
      setMessage(`Logged workout "${workoutName}" • Total Volume: ${res.total_volume_kg} kg`);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to log workout session');
    } finally {
      setLogging(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-400">Loading Workout Planner & Logger...</div>;
  }

  const currentDay = plan?.days?.[selectedDayIdx];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Workout Planner & Performance Logger</h1>
          <p className="text-sm text-gray-400">
            Periodized split generation, set-by-set RPE logging, and deterministic progressive overload
          </p>
        </div>
        <button
          onClick={handleGeneratePlan}
          disabled={generating}
          className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl flex items-center gap-2 self-start"
        >
          <Sparkles className="w-4 h-4" />
          <span>{generating ? 'Synthesizing Split...' : plan ? 'Regenerate Workout Plan' : 'Generate AI Workout Plan'}</span>
        </button>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-3">
          <CheckCircle className="w-5 h-5 flex-shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active Workout Plan View */}
      {plan ? (
        <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-gray-800 pb-4">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-brand-400">
                Active Program • {plan.split_type.replace('_', ' ')}
              </span>
              <h2 className="text-xl font-bold text-white mt-0.5">{plan.name}</h2>
              {plan.coach_notes && <p className="text-xs text-gray-400 mt-1">{plan.coach_notes}</p>}
            </div>
            <div className="text-xs text-gray-400">
              {plan.days_per_week} Days/Week • Week {plan.week_number}
            </div>
          </div>

          {/* Day Selector Tabs */}
          <div className="flex flex-wrap gap-2">
            {plan.days?.map((day: any, idx: number) => (
              <button
                key={day.id || idx}
                onClick={() => {
                  setSelectedDayIdx(idx);
                  setWorkoutName(day.day_name);
                }}
                className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-colors ${
                  selectedDayIdx === idx
                    ? 'bg-brand-600/20 border-brand-500 text-brand-400'
                    : 'bg-gray-900 border-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                Day {idx + 1}: {day.day_name}
              </button>
            ))}
          </div>

          {/* Selected Day Exercises */}
          {currentDay && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-800 text-[11px] font-semibold uppercase text-gray-400">
                    <th className="py-3 px-3">#</th>
                    <th className="py-3 px-3">Exercise</th>
                    <th className="py-3 px-3">Working Sets</th>
                    <th className="py-3 px-3">Rep Target</th>
                    <th className="py-3 px-3">Target RPE</th>
                    <th className="py-3 px-3">Rest</th>
                    <th className="py-3 px-3">Progression Rule</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60 text-sm">
                  {currentDay.exercises?.map((ex: any, i: number) => (
                    <tr key={i} className="hover:bg-gray-900/40">
                      <td className="py-3 px-3 text-gray-500">{ex.order_index}</td>
                      <td className="py-3 px-3 font-medium text-white">{ex.exercise_name}</td>
                      <td className="py-3 px-3 text-gray-300">{ex.sets}</td>
                      <td className="py-3 px-3 text-brand-400 font-medium">
                        {ex.rep_min}–{ex.rep_max} reps
                      </td>
                      <td className="py-3 px-3 text-amber-400">RPE {ex.target_rpe}</td>
                      <td className="py-3 px-3 text-gray-400">{ex.rest_seconds}s</td>
                      <td className="py-3 px-3 text-xs text-gray-400">{ex.progression_rule}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="p-8 bg-dark-800 border border-gray-800 rounded-2xl text-center space-y-3">
          <Dumbbell className="w-10 h-10 text-brand-500 mx-auto" />
          <h3 className="text-lg font-bold text-white">No Active Workout Plan Yet</h3>
          <p className="text-xs text-gray-400 max-w-md mx-auto">
            Click &ldquo;Generate AI Workout Plan&rdquo; above to build a periodized training program tailored to your
            available equipment and weekly schedule.
          </p>
        </div>
      )}

      {/* Interactive Workout Session Logger */}
      <div className="grid lg:grid-cols-3 gap-6">
        <form onSubmit={handleLogSession} className="lg:col-span-2 bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <div>
              <h3 className="text-lg font-bold text-white">Log Completed Workout Session</h3>
              <p className="text-xs text-gray-400">
                Calculates session tonnage, Epley 1RM personal records, and next-session load prescriptions
              </p>
            </div>
            <button
              type="button"
              onClick={handleAddSet}
              className="px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-700 hover:border-brand-500 text-xs text-gray-200 flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Set</span>
            </button>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Session Name</label>
              <input
                type="text"
                required
                value={workoutName}
                onChange={(e) => setWorkoutName(e.target.value)}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Overall Session RPE (1-10)</label>
              <input
                type="number"
                step="0.5"
                min={1}
                max={10}
                value={sessionRpe}
                onChange={(e) => setSessionRpe(Number(e.target.value))}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>
          </div>

          <div className="space-y-2.5">
            <div className="grid grid-cols-12 gap-2 text-[11px] font-semibold uppercase text-gray-400 px-1">
              <div className="col-span-5">Exercise Name</div>
              <div className="col-span-2">Set #</div>
              <div className="col-span-2">Load (kg)</div>
              <div className="col-span-2">Reps</div>
              <div className="col-span-1"></div>
            </div>
            {sets.map((s, idx) => (
              <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                <div className="col-span-5">
                  <input
                    type="text"
                    required
                    value={s.exercise_name}
                    onChange={(e) => {
                      const next = [...sets];
                      next[idx].exercise_name = e.target.value;
                      setSets(next);
                    }}
                    className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
                  />
                </div>
                <div className="col-span-2">
                  <input
                    type="number"
                    min={1}
                    value={s.set_number}
                    onChange={(e) => {
                      const next = [...sets];
                      next[idx].set_number = Number(e.target.value);
                      setSets(next);
                    }}
                    className="w-full px-2.5 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
                  />
                </div>
                <div className="col-span-2">
                  <input
                    type="number"
                    step="0.5"
                    min={0}
                    value={s.weight_kg}
                    onChange={(e) => {
                      const next = [...sets];
                      next[idx].weight_kg = Number(e.target.value);
                      setSets(next);
                    }}
                    className="w-full px-2.5 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
                  />
                </div>
                <div className="col-span-2">
                  <input
                    type="number"
                    min={1}
                    value={s.reps_completed}
                    onChange={(e) => {
                      const next = [...sets];
                      next[idx].reps_completed = Number(e.target.value);
                      setSets(next);
                    }}
                    className="w-full px-2.5 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
                  />
                </div>
                <div className="col-span-1 text-right">
                  <button
                    type="button"
                    onClick={() => handleRemoveSet(idx)}
                    className="p-1.5 text-gray-500 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            type="submit"
            disabled={logging}
            className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-colors"
          >
            {logging ? 'Recording Session & Computing Overload...' : 'Save Workout Session'}
          </button>
        </form>

        {/* Next-Session Progressive Overload & PRs Sidebar */}
        <div className="space-y-6">
          {lastSessionResult && (
            <div className="p-5 bg-dark-800 border border-brand-500/40 rounded-2xl space-y-3">
              <div className="flex items-center gap-2 text-brand-400 text-xs font-semibold uppercase">
                <TrendingUp className="w-4 h-4" />
                <span>Next-Session Load Prescriptions</span>
              </div>
              {lastSessionResult.next_session_prescriptions?.map((p: any, i: number) => (
                <div key={i} className="p-3 rounded-xl bg-gray-900 border border-gray-800 text-xs space-y-1">
                  <div className="font-semibold text-white">{p.exercise_name}</div>
                  <div className="text-emerald-400 font-medium">
                    Next Load: {p.next_weight_kg} kg ({p.action.replace('_', ' ')})
                  </div>
                  <div className="text-gray-400">{p.rationale}</div>
                </div>
              ))}
            </div>
          )}

          <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl space-y-3">
            <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase">
              <Award className="w-4 h-4" />
              <span>Personal Records (Epley 1RM)</span>
            </div>
            {prs.length > 0 ? (
              <div className="space-y-2">
                {prs.map((pr, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-gray-900 border border-gray-800 flex justify-between items-center">
                    <div>
                      <div className="text-xs font-semibold text-white">{pr.exercise_name}</div>
                      <div className="text-[11px] text-gray-400">
                        {pr.weight_kg} kg × {pr.reps} reps
                      </div>
                    </div>
                    <div className="text-sm font-bold text-amber-400">{pr.estimated_1rm_kg} kg</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400">Log a workout session to compute 1RM records.</p>
            )}
          </div>

          <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl space-y-3">
            <div className="flex items-center gap-2 text-gray-300 text-xs font-semibold uppercase">
              <History className="w-4 h-4" />
              <span>Recent Sessions ({sessions.length})</span>
            </div>
            {sessions.slice(0, 5).map((s) => (
              <div key={s.id} className="p-3 rounded-xl bg-gray-900 border border-gray-800 flex justify-between items-center text-xs">
                <div>
                  <div className="font-medium text-white">{s.workout_name}</div>
                  <div className="text-gray-500">RPE {s.session_rpe || '—'}</div>
                </div>
                <div className="font-semibold text-brand-400">{s.total_volume_kg} kg vol</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
