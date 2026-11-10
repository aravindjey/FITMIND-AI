'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { CheckCircle, ArrowRight, ArrowLeft, AlertCircle, Dumbbell, Utensils, User } from 'lucide-react';

const EQUIPMENT_OPTIONS = ['bodyweight', 'dumbbell', 'barbell', 'cables', 'machine', 'full_gym'];
const DAY_OPTIONS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const STAPLE_SUGGESTIONS = ['Roti / Chapati', 'Basmati Rice', 'Moong / Toor Dal', 'Low-Fat Paneer', 'Dahi / Curd', 'Whole Eggs', 'Chicken Breast', 'Rolled Oats', 'Soya Chunks', 'Rajma / Chana'];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    age: 25,
    sex: 'male',
    height_cm: 175,
    current_weight_kg: 72,
    timezone: 'Asia/Kolkata',
    occupation_type: 'Software / Desk Professional',
    activity_level: 'moderately_active',
    primary_goal: 'muscle_gain',
    target_weight_kg: 76,
    sport_name: '',
    sport_position: '',
    training_experience_years: 1.5,
    days_per_week: 4,
    preferred_days: ['Mon', 'Tue', 'Thu', 'Fri'],
    session_duration_minutes: 60,
    available_equipment: ['bodyweight', 'dumbbell', 'barbell'],
    dietary_type: 'vegetarian',
    weekly_food_budget_inr: 2500,
    meals_per_day: 4,
    staple_foods_str: 'Roti / Chapati, Basmati Rice, Moong / Toor Dal, Low-Fat Paneer, Dahi / Curd',
    liked_foods_str: 'Rolled Oats, Banana, Soya Chunks',
    disliked_foods_str: '',
    allergies_str: '',
    avoided_foods_str: '',
  });

  const toggleItem = (list: string[], value: string): string[] =>
    list.includes(value) ? list.filter((i) => i !== value) : [...list, value];

  const splitCsv = (val: string) =>
    val
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

  const handleComplete = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      await apiClient.completeOnboarding({
        age: Number(form.age),
        sex: form.sex,
        height_cm: Number(form.height_cm),
        current_weight_kg: Number(form.current_weight_kg),
        timezone: form.timezone,
        occupation_type: form.occupation_type,
        activity_level: form.activity_level,
        primary_goal: form.primary_goal,
        target_weight_kg: Number(form.target_weight_kg),
        sport_name: form.sport_name || undefined,
        sport_position: form.sport_position || undefined,
        training_experience_years: Number(form.training_experience_years),
        days_per_week: Number(form.days_per_week),
        preferred_days: form.preferred_days,
        session_duration_minutes: Number(form.session_duration_minutes),
        available_equipment: form.available_equipment,
        dietary_type: form.dietary_type,
        weekly_food_budget_inr: Number(form.weekly_food_budget_inr),
        currency_code: 'INR',
        meals_per_day: Number(form.meals_per_day),
        staple_foods: splitCsv(form.staple_foods_str),
        liked_foods: splitCsv(form.liked_foods_str),
        disliked_foods: splitCsv(form.disliked_foods_str),
        allergies: splitCsv(form.allergies_str),
        avoided_foods: splitCsv(form.avoided_foods_str),
      });
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Failed to complete onboarding.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">FITMIND AI Athlete Onboarding</h1>
        <p className="text-sm text-gray-400">
          Intelligent Fitness. Science-Driven Results. Establish your authoritative biometric baseline, equipment setup, and real-world Indian / global dietary preferences.
        </p>
      </div>

      {/* Stepper */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { num: 1, label: 'Biometrics & Goal', icon: User },
          { num: 2, label: 'Training & Equipment', icon: Dumbbell },
          { num: 3, label: 'Foods & INR Budget', icon: Utensils },
        ].map((s) => {
          const Icon = s.icon;
          const active = step === s.num;
          const done = step > s.num;
          return (
            <button
              key={s.num}
              type="button"
              onClick={() => setStep(s.num)}
              className={`p-4 rounded-xl border text-left transition-all flex items-center gap-3 ${
                active
                  ? 'bg-brand-500/10 border-brand-500 text-white'
                  : done
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-dark-800 border-gray-800 text-gray-400'
              }`}
            >
              <Icon className="w-5 h-5 shrink-0" />
              <div>
                <div className="text-xs uppercase font-semibold opacity-75">Step {s.num}</div>
                <div className="text-sm font-bold">{s.label}</div>
              </div>
            </button>
          );
        })}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleComplete} className="bg-dark-800 border border-gray-800 rounded-2xl p-8 space-y-6">
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-lg font-bold text-white border-b border-gray-800 pb-3">
              Step 1: Personal Biometrics, Lifestyle & Primary Goal
            </h2>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Age (Years)</label>
                <input
                  type="number"
                  required
                  min={13}
                  max={100}
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Biological Sex</label>
                <select
                  value={form.sex}
                  onChange={(e) => setForm({ ...form, sex: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Height (cm)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={form.height_cm}
                  onChange={(e) => setForm({ ...form, height_cm: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Current Body Weight (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={form.current_weight_kg}
                  onChange={(e) => setForm({ ...form, current_weight_kg: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Primary Athletic Goal</label>
                <select
                  value={form.primary_goal}
                  onChange={(e) => setForm({ ...form, primary_goal: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                >
                  <option value="muscle_gain">Muscle Gain (Hypertrophy)</option>
                  <option value="fat_loss">Fat Loss & Body Recomposition</option>
                  <option value="strength">Strength Development</option>
                  <option value="powerlifting">Powerlifting (Squat/Bench/Deadlift)</option>
                  <option value="bodybuilding">Bodybuilding Aesthetics</option>
                  <option value="sports_performance">Sports Performance</option>
                  <option value="general_fitness">General Health & Fitness</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Target Weight (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  value={form.target_weight_kg}
                  onChange={(e) => setForm({ ...form, target_weight_kg: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Daily Activity Level</label>
                <select
                  value={form.activity_level}
                  onChange={(e) => setForm({ ...form, activity_level: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                >
                  <option value="sedentary">Sedentary (Desk Job, &lt;5k steps)</option>
                  <option value="lightly_active">Lightly Active (1-2 days exercise)</option>
                  <option value="moderately_active">Moderately Active (3-5 days training)</option>
                  <option value="very_active">Very Active (6-7 days intense training)</option>
                  <option value="extra_active">Extra Active (Physical job / 2x daily)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Occupation / Student Status</label>
                <input
                  type="text"
                  value={form.occupation_type}
                  onChange={(e) => setForm({ ...form, occupation_type: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-xl text-sm flex items-center gap-2"
              >
                <span>Next: Training Setup</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-lg font-bold text-white border-b border-gray-800 pb-3">
              Step 2: Training Experience, Schedule & Equipment
            </h2>

            <div className="grid sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Training Experience (Years)</label>
                <input
                  type="number"
                  step="0.5"
                  min={0}
                  value={form.training_experience_years}
                  onChange={(e) => setForm({ ...form, training_experience_years: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Training Days / Week</label>
                <select
                  value={form.days_per_week}
                  onChange={(e) => setForm({ ...form, days_per_week: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                >
                  {[2, 3, 4, 5, 6].map((d) => (
                    <option key={d} value={d}>{d} Days / Week</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Session Duration (Mins)</label>
                <input
                  type="number"
                  step={15}
                  min={20}
                  max={180}
                  value={form.session_duration_minutes}
                  onChange={(e) => setForm({ ...form, session_duration_minutes: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Available Equipment</label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {EQUIPMENT_OPTIONS.map((eq) => {
                  const selected = form.available_equipment.includes(eq);
                  return (
                    <button
                      key={eq}
                      type="button"
                      onClick={() =>
                        setForm({ ...form, available_equipment: toggleItem(form.available_equipment, eq) })
                      }
                      className={`px-4 py-2.5 rounded-xl border text-xs font-semibold uppercase tracking-wider transition-colors ${
                        selected
                          ? 'bg-brand-500/20 border-brand-500 text-brand-500'
                          : 'bg-gray-900 border-gray-800 text-gray-400'
                      }`}
                    >
                      {eq.replace('_', ' ')}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Preferred Training Days</label>
              <div className="flex flex-wrap gap-2">
                {DAY_OPTIONS.map((d) => {
                  const selected = form.preferred_days.includes(d);
                  return (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setForm({ ...form, preferred_days: toggleItem(form.preferred_days, d) })}
                      className={`px-3.5 py-2 rounded-lg border text-xs font-bold transition-colors ${
                        selected
                          ? 'bg-brand-500 text-white border-brand-500'
                          : 'bg-gray-900 border-gray-800 text-gray-400'
                      }`}
                    >
                      {d}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-5 py-2.5 bg-gray-900 border border-gray-800 text-gray-300 rounded-xl text-sm flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-xl text-sm flex items-center gap-2"
              >
                <span>Next: Nutrition & INR Budget</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-lg font-bold text-white border-b border-gray-800 pb-3">
              Step 3: Food Preferences, Restrictions & Weekly Budget (INR ₹)
            </h2>

            <div className="grid sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Dietary Pattern</label>
                <select
                  value={form.dietary_type}
                  onChange={(e) => setForm({ ...form, dietary_type: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                >
                  <option value="vegetarian">Indian Vegetarian (Dairy Allowed)</option>
                  <option value="eggetarian">Eggetarian (Veg + Eggs)</option>
                  <option value="omnivore">Non-Vegetarian / Omnivore</option>
                  <option value="vegan">Strict Vegan (Plant-Only)</option>
                  <option value="jain">Jain Dietary Constraints</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Weekly Food Budget (₹ INR)</label>
                <input
                  type="number"
                  step={100}
                  min={500}
                  required
                  value={form.weekly_food_budget_inr}
                  onChange={(e) => setForm({ ...form, weekly_food_budget_inr: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Preferred Meals / Day</label>
                <select
                  value={form.meals_per_day}
                  onChange={(e) => setForm({ ...form, meals_per_day: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                >
                  {[3, 4, 5].map((m) => (
                    <option key={m} value={m}>{m} Meals / Day</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">
                What staple foods do you normally eat and have easily available? (Comma-separated)
              </label>
              <input
                type="text"
                value={form.staple_foods_str}
                onChange={(e) => setForm({ ...form, staple_foods_str: e.target.value })}
                className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
              <div className="flex flex-wrap gap-1.5 mt-2">
                {STAPLE_SUGGESTIONS.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => {
                      const cur = splitCsv(form.staple_foods_str);
                      if (!cur.includes(item)) {
                        setForm({ ...form, staple_foods_str: [...cur, item].join(', ') });
                      }
                    }}
                    className="px-2.5 py-1 rounded-md bg-gray-900 border border-gray-800 text-xs text-gray-400 hover:text-brand-500"
                  >
                    + {item}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">
                  Food Allergies (Strictly Excluded)
                </label>
                <input
                  type="text"
                  placeholder="e.g., peanuts, shellfish, lactose"
                  value={form.allergies_str}
                  onChange={(e) => setForm({ ...form, allergies_str: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">
                  Disliked or Avoided Foods
                </label>
                <input
                  type="text"
                  placeholder="e.g., mushrooms, bitter gourd"
                  value={form.disliked_foods_str}
                  onChange={(e) => setForm({ ...form, disliked_foods_str: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
                />
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-5 py-2.5 bg-gray-900 border border-gray-800 text-gray-300 rounded-xl text-sm flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>

              <button
                type="submit"
                disabled={saving}
                className="px-8 py-3.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-bold rounded-xl text-sm flex items-center gap-2 shadow-xl shadow-brand-600/25"
              >
                <CheckCircle className="w-4 h-4" />
                <span>{saving ? 'Calculating BMR/TDEE & Saving...' : 'Complete Onboarding & Save'}</span>
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
