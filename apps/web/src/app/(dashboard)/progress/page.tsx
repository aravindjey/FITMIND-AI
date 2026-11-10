'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import {
  TrendingUp,
  Award,
  Ruler,
  CheckCircle,
  AlertCircle,
  Sparkles,
  Plus,
} from 'lucide-react';

export default function ProgressPage() {
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [measurements, setMeasurements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    waist_cm: 80,
    chest_cm: 100,
    hips_cm: 95,
    shoulders_cm: 118,
    bicep_left_cm: 36,
    bicep_right_cm: 36.5,
    thigh_left_cm: 56,
    thigh_right_cm: 56,
    notes: '',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [aRes, mRes] = await Promise.all([
        apiClient.getProgressAnalytics(),
        apiClient.listBodyMeasurements(),
      ]);
      setAnalytics(aRes);
      setMeasurements(mRes || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load progress analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleLogMeasurement = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await apiClient.createBodyMeasurement({
        waist_cm: Number(form.waist_cm),
        chest_cm: Number(form.chest_cm),
        hips_cm: Number(form.hips_cm),
        shoulders_cm: Number(form.shoulders_cm),
        bicep_left_cm: Number(form.bicep_left_cm),
        bicep_right_cm: Number(form.bicep_right_cm),
        thigh_left_cm: Number(form.thigh_left_cm),
        thigh_right_cm: Number(form.thigh_right_cm),
        notes: form.notes || undefined,
      });
      setMessage('Body circumference measurements recorded to historical database.');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to record measurements');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-400">Loading Progress Analytics & EMA Trends...</div>;
  }

  const aiInsight = analytics?.progress_agent_insight;
  const weightSeries = analytics?.weight_series || [];
  const volumeSeries = analytics?.workout_volume_series || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Progress Analytics & Body Measurements</h1>
        <p className="text-sm text-gray-400">
          7-day Exponential Moving Average (EMA) weight trends, session tonnage, and circumference tracking
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

      {/* ProgressAgent Synthesis Banner */}
      {aiInsight && (
        <div className="p-6 bg-dark-800 border border-brand-500/30 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase text-brand-400">
              <Sparkles className="w-4 h-4" />
              <span>ProgressAgent Trajectory Analysis</span>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-brand-500/10 text-xs text-brand-300 font-medium capitalize">
              Status: {(aiInsight.trajectory_status || 'on_track').replace('_', ' ')}
            </span>
          </div>
          <p className="text-sm text-gray-200 leading-relaxed">{aiInsight.insight}</p>
          <div className="grid sm:grid-cols-3 gap-4 pt-2 border-t border-gray-800 text-xs">
            <div>
              <span className="text-gray-400">7-Day EMA Weight: </span>
              <span className="text-white font-semibold">{aiInsight.ema_weight_kg} kg</span>
            </div>
            <div>
              <span className="text-gray-400">Weekly Velocity: </span>
              <span className="text-white font-semibold">{aiInsight.weekly_rate_kg} kg/wk</span>
            </div>
            <div>
              <span className="text-gray-400">Personal Records Achieved: </span>
              <span className="text-emerald-400 font-semibold">{aiInsight.pr_count} PRs</span>
            </div>
          </div>
        </div>
      )}

      {/* Weight History & Workout Tonnage */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-brand-500" />
              <span>Body Weight History ({weightSeries.length} entries)</span>
            </h3>
            <span className="text-xs text-gray-400">7d EMA: {analytics?.ema_weight_kg || '—'} kg</span>
          </div>
          {weightSeries.length > 0 ? (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {weightSeries.map((w: any, i: number) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-gray-900 border border-gray-800 flex justify-between items-center text-xs"
                >
                  <span className="text-gray-400">{w.date}</span>
                  <span className="font-bold text-white">{w.weight_kg} kg</span>
                  <span className="text-gray-500">EMA: {w.ema_kg} kg</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-400">No weight records yet.</p>
          )}
        </div>

        <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl space-y-4">
          <h3 className="font-bold text-white flex items-center gap-2">
            <Award className="w-4 h-4 text-amber-400" />
            <span>Workout Volume & Personal Records</span>
          </h3>
          {volumeSeries.length > 0 ? (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {volumeSeries.map((v: any, i: number) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-gray-900 border border-gray-800 flex justify-between items-center text-xs"
                >
                  <div>
                    <div className="font-semibold text-white">{v.workout_name}</div>
                    <div className="text-gray-500">{v.date}</div>
                  </div>
                  <div className="text-brand-400 font-bold">{v.total_volume_kg} kg tonnage</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-400">Log workouts to track session tonnage over time.</p>
          )}
        </div>
      </div>

      {/* Body Circumference Logger & History */}
      <div className="grid lg:grid-cols-2 gap-6">
        <form onSubmit={handleLogMeasurement} className="p-6 bg-dark-800 border border-gray-800 rounded-2xl space-y-4">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3 flex items-center gap-2">
            <Ruler className="w-5 h-5 text-brand-400" />
            <span>Log Tape Circumference Measurements (cm)</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Waist (cm)</label>
              <input
                type="number"
                step="0.1"
                value={form.waist_cm}
                onChange={(e) => setForm({ ...form, waist_cm: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Chest (cm)</label>
              <input
                type="number"
                step="0.1"
                value={form.chest_cm}
                onChange={(e) => setForm({ ...form, chest_cm: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Hips (cm)</label>
              <input
                type="number"
                step="0.1"
                value={form.hips_cm}
                onChange={(e) => setForm({ ...form, hips_cm: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Shoulders (cm)</label>
              <input
                type="number"
                step="0.1"
                value={form.shoulders_cm}
                onChange={(e) => setForm({ ...form, shoulders_cm: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Left Arm (cm)</label>
              <input
                type="number"
                step="0.1"
                value={form.bicep_left_cm}
                onChange={(e) => setForm({ ...form, bicep_left_cm: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Right Arm (cm)</label>
              <input
                type="number"
                step="0.1"
                value={form.bicep_right_cm}
                onChange={(e) => setForm({ ...form, bicep_right_cm: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Left Thigh (cm)</label>
              <input
                type="number"
                step="0.1"
                value={form.thigh_left_cm}
                onChange={(e) => setForm({ ...form, thigh_left_cm: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Right Thigh (cm)</label>
              <input
                type="number"
                step="0.1"
                value={form.thigh_right_cm}
                onChange={(e) => setForm({ ...form, thigh_right_cm: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-white text-xs"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>{saving ? 'Recording Measurements...' : 'Save Tape Measurements'}</span>
          </button>
        </form>

        <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl space-y-4">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3">
            Recorded Circumference History ({measurements.length})
          </h3>
          {measurements.length > 0 ? (
            <div className="space-y-2.5 max-h-64 overflow-y-auto">
              {measurements.map((m: any) => (
                <div key={m.id} className="p-3.5 rounded-xl bg-gray-900 border border-gray-800 text-xs space-y-1">
                  <div className="flex justify-between font-semibold text-white">
                    <span>{m.recorded_at}</span>
                    <span className="text-brand-400">{m.weight_kg} kg</span>
                  </div>
                  <div className="text-gray-400">
                    Waist: {m.waist_cm || '—'}cm • Chest: {m.chest_cm || '—'}cm • Hips: {m.hips_cm || '—'}cm • Arms:{' '}
                    {m.bicep_right_cm || '—'}cm
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-400 py-8 text-center">No circumference measurements logged yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
