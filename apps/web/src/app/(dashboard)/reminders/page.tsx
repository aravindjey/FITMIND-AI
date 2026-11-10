'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Bell, Plus, Trash2, Clock, CheckCircle, AlertCircle } from 'lucide-react';

export default function RemindersPage() {
  const [reminders, setReminders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    title: 'Evening Hypertrophy Training Session',
    message: 'Pre-workout meal 90 mins prior + 500ml water hydration check',
    notification_type: 'workout',
    scheduled_time: '18:00',
  });

  const loadReminders = async () => {
    setLoading(true);
    try {
      const list = await apiClient.listReminders();
      setReminders(list || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReminders();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    setMessage(null);
    try {
      await apiClient.createReminder({
        title: form.title,
        message: form.message,
        notification_type: form.notification_type,
        scheduled_time: form.scheduled_time,
        days_of_week: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      });
      setMessage(`Scheduled reminder "${form.title}" at ${form.scheduled_time}`);
      await loadReminders();
    } catch (err: any) {
      setError(err.message || 'Failed to create reminder');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    await apiClient.deleteReminder(id);
    await loadReminders();
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Reminders, Hydration & Schedule Automation</h1>
        <p className="text-sm text-gray-400">
          Persistent scheduled notifications for workouts, Indian meal prep, hydration, check-ins, and sleep wind-down
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

      <div className="grid lg:grid-cols-2 gap-6">
        <form onSubmit={handleCreate} className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3 flex items-center gap-2">
            <Bell className="w-5 h-5 text-brand-400" />
            <span>Create Scheduled Reminder</span>
          </h3>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Reminder Title</label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full px-3.5 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            />
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Category</label>
              <select
                value={form.notification_type}
                onChange={(e) => setForm({ ...form, notification_type: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              >
                <option value="workout">Workout Session</option>
                <option value="meal">Meal & Protein Timing</option>
                <option value="hydration">Hydration Check</option>
                <option value="check_in">Morning Check-In & Weigh-In</option>
                <option value="sleep">Sleep Wind-Down</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Scheduled Time (24h)</label>
              <input
                type="time"
                required
                value={form.scheduled_time}
                onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Protocol Notes</label>
            <input
              type="text"
              value={form.message}
              onChange={(e) => setForm({ ...form, message: e.target.value })}
              className="w-full px-3.5 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={creating}
            className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>{creating ? 'Scheduling Reminder...' : 'Save Scheduled Reminder'}</span>
          </button>
        </form>

        <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3">
            Active Athlete Reminders ({reminders.length})
          </h3>
          {loading ? (
            <div className="text-xs text-gray-400 py-8 text-center">Loading reminders...</div>
          ) : reminders.length > 0 ? (
            <div className="space-y-3">
              {reminders.map((r) => (
                <div
                  key={r.id}
                  className="p-4 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-brand-500/15 text-brand-400 text-[11px] font-semibold uppercase">
                        {r.notification_type.replace('_', ' ')}
                      </span>
                      <span className="text-xs font-bold text-white flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-gray-400" />
                        {r.scheduled_time}
                      </span>
                    </div>
                    <div className="text-sm font-semibold text-white">{r.title}</div>
                    {r.message && <div className="text-xs text-gray-400">{r.message}</div>}
                  </div>
                  <button
                    onClick={() => handleDelete(r.id)}
                    className="p-2 text-gray-500 hover:text-red-400 transition-colors"
                    title="Delete Reminder"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-400 py-8 text-center">
              No scheduled reminders configured yet. Create your first workout, meal, or hydration reminder on the left.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
