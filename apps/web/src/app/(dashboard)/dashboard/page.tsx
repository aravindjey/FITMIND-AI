'use client';
import { useEffect, useState } from 'react';
import { apiClient, AthleteProfile } from '@/lib/api-client';
import EmptyState from '@/components/EmptyState';
import { User, Dumbbell, Utensils, Calendar } from 'lucide-react';

export default function DashboardPage() {
  const [profile, setProfile] = useState<AthleteProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .getProfile()
      .then((data) => setProfile(data))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-gray-400">
        <span>Loading Athlete Profile...</span>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Athlete Overview</h1>
          <p className="text-sm text-gray-400">Your current athletic status and active plans</p>
        </div>

        <EmptyState
          icon={User}
          title="No Athlete Profile Found"
          description="You have not created an athlete profile yet. Set up your height, weight, activity level, and goals to activate your dashboard."
          actionText="Create Athlete Profile"
          actionHref="/profile"
        />
      </div>
    );
  }

  const primaryGoal = profile.goals && profile.goals.length > 0 ? profile.goals[0].primary_goal : 'Not set';

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Athlete Overview</h1>
        <p className="text-sm text-gray-400">Authoritative baseline metrics from database</p>
      </div>

      {/* Profile Metrics Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Body Weight</div>
          <div className="text-2xl font-bold text-white">{profile.current_weight_kg} <span className="text-sm font-normal text-gray-400">kg</span></div>
        </div>

        <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Height</div>
          <div className="text-2xl font-bold text-white">{profile.height_cm} <span className="text-sm font-normal text-gray-400">cm</span></div>
        </div>

        <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Primary Goal</div>
          <div className="text-2xl font-bold text-brand-500 capitalize">{primaryGoal.replace('_', ' ')}</div>
        </div>

        <div className="p-5 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Experience</div>
          <div className="text-2xl font-bold text-white">{profile.training_experience_years} <span className="text-sm font-normal text-gray-400">yrs</span></div>
        </div>
      </div>

      {/* Plan Status Sections (Empty States for Phase 1) */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500">
              <Dumbbell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white">Active Workout Plan</h3>
              <p className="text-xs text-gray-400">Periodized training program</p>
            </div>
          </div>
          <EmptyState
            icon={Calendar}
            title="No Active Workout Plan"
            description="AI Workout Generation engine will be activated in Phase 3."
          />
        </div>

        <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500">
              <Utensils className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white">Active Nutrition Plan</h3>
              <p className="text-xs text-gray-400">Constraint-aware meal strategy</p>
            </div>
          </div>
          <EmptyState
            icon={Utensils}
            title="No Active Nutrition Plan"
            description="Constraint-aware AI Nutrition Agent will be activated in Phase 3."
          />
        </div>
      </div>
    </div>
  );
}
