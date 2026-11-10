'use client';
import { useEffect, useState } from 'react';
import { apiClient, AthleteProfile } from '@/lib/api-client';
import { User, Save, CheckCircle, AlertCircle } from 'lucide-react';

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    age: 25,
    sex: 'male',
    height_cm: 175,
    current_weight_kg: 70,
    timezone: 'Asia/Kolkata',
    training_experience_years: 2,
    activity_level: 'moderately_active',
    occupation_type: '',
    sport_name: '',
    sport_position: '',
    primary_goal: 'muscle_gain',
    target_weight_kg: 75,
  });

  useEffect(() => {
    apiClient
      .getProfile()
      .then((data) => {
        setHasProfile(true);
        setFormData({
          age: data.age,
          sex: data.sex,
          height_cm: data.height_cm,
          current_weight_kg: data.current_weight_kg,
          timezone: data.timezone || 'Asia/Kolkata',
          training_experience_years: data.training_experience_years,
          activity_level: data.activity_level,
          occupation_type: data.occupation_type || '',
          sport_name: data.sport_name || '',
          sport_position: data.sport_position || '',
          primary_goal: data.goals && data.goals.length > 0 ? data.goals[0].primary_goal : 'muscle_gain',
          target_weight_kg: data.goals && data.goals.length > 0 && data.goals[0].target_weight_kg ? data.goals[0].target_weight_kg : 75,
        });
      })
      .catch(() => {
        setHasProfile(false);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(null);
    setError(null);

    const payload = {
      age: Number(formData.age),
      sex: formData.sex,
      height_cm: Number(formData.height_cm),
      current_weight_kg: Number(formData.current_weight_kg),
      timezone: formData.timezone,
      training_experience_years: Number(formData.training_experience_years),
      activity_level: formData.activity_level,
      occupation_type: formData.occupation_type || undefined,
      sport_name: formData.sport_name || undefined,
      sport_position: formData.sport_position || undefined,
      goal: {
        primary_goal: formData.primary_goal,
        target_weight_kg: Number(formData.target_weight_kg),
      },
    };

    try {
      if (hasProfile) {
        await apiClient.updateProfile(payload);
      } else {
        await apiClient.createProfile(payload);
        setHasProfile(true);
      }
      setSuccess('Athlete profile successfully saved to authoritative database!');
    } catch (err: any) {
      setError(err.message || 'Failed to save profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-gray-400">
        <span>Loading Profile Form...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">FITMIND AI Athlete Profile</h1>
        <p className="text-sm text-gray-400">
          Intelligent Fitness. Science-Driven Results. • Authoritative athlete baseline metrics and goals
        </p>
      </div>

      {success && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-3">
          <CheckCircle className="w-5 h-5 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 bg-dark-800 border border-gray-800 p-8 rounded-2xl">
        <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-3">Biometric Baseline</h3>
        
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Age</label>
            <input
              type="number"
              required
              value={formData.age}
              onChange={(e) => setFormData({ ...formData, age: Number(e.target.value) })}
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Sex</label>
            <select
              value={formData.sex}
              onChange={(e) => setFormData({ ...formData, sex: e.target.value })}
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Height (cm)</label>
            <input
              type="number"
              step="0.1"
              required
              value={formData.height_cm}
              onChange={(e) => setFormData({ ...formData, height_cm: Number(e.target.value) })}
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Current Weight (kg)</label>
            <input
              type="number"
              step="0.1"
              required
              value={formData.current_weight_kg}
              onChange={(e) => setFormData({ ...formData, current_weight_kg: Number(e.target.value) })}
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            />
          </div>
        </div>

        <h3 className="text-lg font-semibold text-white border-b border-gray-800 pb-3 pt-4">Training & Lifestyle</h3>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Training Experience (years)</label>
            <input
              type="number"
              step="0.5"
              required
              value={formData.training_experience_years}
              onChange={(e) => setFormData({ ...formData, training_experience_years: Number(e.target.value) })}
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Activity Level</label>
            <select
              value={formData.activity_level}
              onChange={(e) => setFormData({ ...formData, activity_level: e.target.value })}
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            >
              <option value="sedentary">Sedentary (Desk Job)</option>
              <option value="lightly_active">Lightly Active (1-2 days/wk)</option>
              <option value="moderately_active">Moderately Active (3-5 days/wk)</option>
              <option value="very_active">Very Active (6-7 days/wk)</option>
              <option value="extra_active">Extra Active (2x per day)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Primary Goal</label>
            <select
              value={formData.primary_goal}
              onChange={(e) => setFormData({ ...formData, primary_goal: e.target.value })}
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            >
              <option value="muscle_gain">Muscle Gain</option>
              <option value="fat_loss">Fat Loss</option>
              <option value="strength">Strength</option>
              <option value="powerlifting">Powerlifting</option>
              <option value="bodybuilding">Bodybuilding</option>
              <option value="sports_performance">Sports Performance</option>
              <option value="general_fitness">General Fitness</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Target Weight (kg)</label>
            <input
              type="number"
              step="0.1"
              value={formData.target_weight_kg}
              onChange={(e) => setFormData({ ...formData, target_weight_kg: Number(e.target.value) })}
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            />
          </div>
        </div>

        {(() => {
          const curW = Number(formData.current_weight_kg);
          const tgtW = Number(formData.target_weight_kg);
          const goal = formData.primary_goal;
          const isMassGoalWithLowerTarget =
            ['muscle_gain', 'bodybuilding', 'strength', 'powerlifting'].includes(goal) &&
            tgtW > 0 &&
            curW - tgtW > 1.0;
          const isFatLossWithHigherTarget =
            goal === 'fat_loss' && tgtW > 0 && tgtW - curW > 1.0;

          if (isMassGoalWithLowerTarget) {
            return (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-amber-200 block mb-0.5">
                    Goal &amp; Target Weight Conflict Detected ({curW} kg → {tgtW} kg with {goal.replace('_', ' ')})
                  </span>
                  Your target weight ({tgtW} kg) is {Math.round((curW - tgtW) * 10) / 10} kg below your current weight ({curW} kg). A calorie surplus (+12%) would increase body weight away from {tgtW} kg. The Nutrition Engine will automatically apply a high-protein body-recomposition deficit (-15% below TDEE, 2.1g/kg protein) unless you increase your target weight above {curW} kg or switch your primary goal to Fat Loss.
                </div>
              </div>
            );
          }
          if (isFatLossWithHigherTarget) {
            return (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-amber-200 block mb-0.5">
                    Goal &amp; Target Weight Conflict Detected ({curW} kg → {tgtW} kg with Fat Loss)
                  </span>
                  Your primary goal is Fat Loss, but your target weight ({tgtW} kg) is above your current weight ({curW} kg). Please verify whether you intend to lose fat (set target weight below {curW} kg) or gain lean mass (switch goal to Muscle Gain).
                </div>
              </div>
            );
          }
          return null;
        })()}

        <button
          type="submit"
          disabled={saving}
          className="px-6 py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors shadow-lg shadow-brand-600/20 text-sm flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving to Database...' : 'Save Profile'}</span>
        </button>
      </form>
    </div>
  );
}
