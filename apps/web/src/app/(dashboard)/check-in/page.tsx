'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import {
  ClipboardCheck,
  Activity,
  Sparkles,
  CheckCircle,
  AlertCircle,
  HeartPulse,
} from 'lucide-react';

export default function CheckInPage() {
  const [data, setData] = useState<any | null>(null);
  const [latestResult, setLatestResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    weight_kg: 72,
    energy_score: 8,
    sleep_hours: 7.5,
    sleep_quality_score: 8,
    stress_score: 3,
    soreness_score: 3,
    hydration_liters: 3.0,
    nutrition_adherence_percent: 90,
    workout_completed: true,
    notes: '',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [cRes, profileRes] = await Promise.all([
        apiClient.listCheckIns(),
        apiClient.getProfile().catch(() => null),
      ]);
      setData(cRes);
      if (profileRes?.current_weight_kg) {
        setForm((prev) => ({ ...prev, weight_kg: profileRes.current_weight_kg }));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      const res = await apiClient.submitDailyCheckIn({
        weight_kg: Number(form.weight_kg),
        energy_score: Number(form.energy_score),
        sleep_hours: Number(form.sleep_hours),
        sleep_quality_score: Number(form.sleep_quality_score),
        stress_score: Number(form.stress_score),
        soreness_score: Number(form.soreness_score),
        hydration_liters: Number(form.hydration_liters),
        nutrition_adherence_percent: Number(form.nutrition_adherence_percent),
        workout_completed: form.workout_completed,
        notes: form.notes || undefined,
      });
      setLatestResult(res);
      const rec = res.recovery_assessment;
      setMessage(
        `Daily check-in recorded! Recovery Readiness Score: ${rec?.readiness_score}/100 (${(rec?.status || '').replace('_', ' ')})`
      );
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to submit daily check-in');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-400">Loading Recovery Readiness & Check-Ins...</div>;
  }

  const readiness = latestResult?.recovery_assessment || data?.latest_recovery;
  const checkIns = data?.check_ins || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Daily Check-In, Recovery & Lifestyle Habits</h1>
        <p className="text-sm text-gray-400">
          Deterministic 0–100 recovery readiness index, training intensity autoregulation, and habit coaching
        </p>
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

      {/* Readiness & AI Agent Insights */}
      {readiness && (
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-5 bg-dark-800 border border-emerald-500/30 rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold uppercase text-emerald-400">
              <span>RecoveryAgent Readiness</span>
              <HeartPulse className="w-4 h-4" />
            </div>
            <div className="text-3xl font-bold text-white">{readiness.readiness_score}/100</div>
            <div className="text-xs text-gray-300 capitalize">
              Status:{' '}
              <span className="font-semibold text-emerald-400">
                {(readiness.status || 'optimal').replace('_', ' ')}
              </span>{' '}
              • Load Modifier: {readiness.intensity_modifier}x
            </div>
            <p className="text-xs text-gray-400">{readiness.recommendation}</p>
          </div>

          {latestResult?.lifestyle_insights && (
            <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold uppercase text-purple-400">
                <span>LifestyleHabitAgent ({latestResult.lifestyle_insights.checkin_streak_days}-Day Streak)</span>
                <Sparkles className="w-4 h-4" />
              </div>
              <ul className="list-disc list-inside text-xs text-gray-300 space-y-1">
                {latestResult.lifestyle_insights.habit_recommendations?.map((h: string, i: number) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Daily Check-In Form */}
        <form onSubmit={handleSubmit} className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3 flex items-center gap-2">
            <ClipboardCheck className="w-5 h-5 text-brand-400" />
            <span>Submit Daily Check-In</span>
          </h3>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Morning Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                required
                value={form.weight_kg}
                onChange={(e) => setForm({ ...form, weight_kg: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Sleep Duration (hours)</label>
              <input
                type="number"
                step="0.5"
                min={0}
                max={16}
                required
                value={form.sleep_hours}
                onChange={(e) => setForm({ ...form, sleep_hours: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Sleep Quality (1–10)</label>
              <input
                type="number"
                min={1}
                max={10}
                value={form.sleep_quality_score}
                onChange={(e) => setForm({ ...form, sleep_quality_score: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Energy Level (1–10)</label>
              <input
                type="number"
                min={1}
                max={10}
                value={form.energy_score}
                onChange={(e) => setForm({ ...form, energy_score: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Muscle Soreness (1–10)</label>
              <input
                type="number"
                min={1}
                max={10}
                value={form.soreness_score}
                onChange={(e) => setForm({ ...form, soreness_score: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Life Stress (1–10)</label>
              <input
                type="number"
                min={1}
                max={10}
                value={form.stress_score}
                onChange={(e) => setForm({ ...form, stress_score: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Water Intake (Liters)</label>
              <input
                type="number"
                step="0.25"
                value={form.hydration_liters}
                onChange={(e) => setForm({ ...form, hydration_liters: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Nutrition Adherence (%)</label>
              <input
                type="number"
                min={0}
                max={100}
                value={form.nutrition_adherence_percent}
                onChange={(e) => setForm({ ...form, nutrition_adherence_percent: Number(e.target.value) })}
                className="w-full px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-colors"
          >
            {submitting ? 'Computing Readiness & Updating Weight Log...' : 'Submit Daily Check-In'}
          </button>
        </form>

        {/* Check-In History */}
        <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3">
            Historical Check-In Log ({checkIns.length})
          </h3>
          {checkIns.length > 0 ? (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {checkIns.map((c: any) => (
                <div key={c.id} className="p-3.5 rounded-xl bg-gray-900 border border-gray-800 text-xs space-y-1">
                  <div className="flex justify-between font-semibold text-white">
                    <span>{c.check_in_date}</span>
                    <span className="text-brand-400">
                      {c.weight_kg} kg (EMA: {c.ema_weight_kg} kg)
                    </span>
                  </div>
                  <div className="text-gray-400">
                    Sleep: {c.sleep_hours}h (Q:{c.sleep_quality_score}/10) • Energy: {c.energy_score}/10 • Soreness:{' '}
                    {c.soreness_score}/10 • Hydration: {c.hydration_liters}L
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-400 py-8 text-center">No daily check-ins recorded yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
