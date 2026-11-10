'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { RefreshCw } from 'lucide-react';

export default function ExercisesPage() {
  const [exercises, setExercises] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [muscleFilter, setMuscleFilter] = useState('');
  const [equipmentFilter, setEquipmentFilter] = useState('');
  const [substitutionResult, setSubstitutionResult] = useState<any | null>(null);

  const loadExercises = async () => {
    setLoading(true);
    try {
      const list = await apiClient.listExercises(muscleFilter || undefined, equipmentFilter || undefined);
      setExercises(list);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExercises();
  }, [muscleFilter, equipmentFilter]);

  const handleFindSubstitutes = async (exerciseName: string) => {
    const res = await apiClient.substituteExercise(exerciseName, ['dumbbell', 'bodyweight', 'cables', 'barbell']);
    setSubstitutionResult(res);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Curated Exercise & Movement Library</h1>
        <p className="text-sm text-gray-400">
          Validated biomechanics catalog with movement-pattern and equipment substitution
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 bg-dark-800 border border-gray-800 p-4 rounded-2xl">
        <div>
          <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Primary Muscle</label>
          <select
            value={muscleFilter}
            onChange={(e) => setMuscleFilter(e.target.value)}
            className="px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-xs"
          >
            <option value="">All Muscle Groups</option>
            <option value="chest">Chest</option>
            <option value="back">Back</option>
            <option value="quads">Quadriceps</option>
            <option value="hamstrings">Hamstrings</option>
            <option value="shoulders">Shoulders</option>
            <option value="biceps">Biceps</option>
            <option value="triceps">Triceps</option>
            <option value="core">Core</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold uppercase text-gray-400 mb-1">Equipment Required</label>
          <select
            value={equipmentFilter}
            onChange={(e) => setEquipmentFilter(e.target.value)}
            className="px-3.5 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-xs"
          >
            <option value="">All Equipment</option>
            <option value="barbell">Barbell</option>
            <option value="dumbbell">Dumbbell</option>
            <option value="bodyweight">Bodyweight</option>
            <option value="cables">Cables</option>
            <option value="machine">Machine</option>
          </select>
        </div>
      </div>

      {substitutionResult && (
        <div className="p-5 bg-brand-600/10 border border-brand-500/30 rounded-2xl space-y-2">
          <div className="text-xs font-semibold text-brand-400 uppercase">
            Biomechanical Substitutes for &ldquo;{substitutionResult.original_exercise}&rdquo;
          </div>
          {substitutionResult.substitutions?.length > 0 ? (
            <div className="grid sm:grid-cols-3 gap-3 pt-1">
              {substitutionResult.substitutions.map((sub: any) => (
                <div key={sub.id} className="p-3 rounded-xl bg-gray-900 border border-gray-800 text-xs">
                  <div className="font-semibold text-white">{sub.name}</div>
                  <div className="text-gray-400 mt-0.5 capitalize">
                    Equipment: {sub.equipment_required} • {sub.primary_muscle_group}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-400">No alternative exercises found for this movement pattern.</p>
          )}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-gray-400">Loading Exercise Library...</div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {exercises.map((ex) => (
            <div key={ex.id} className="p-5 bg-dark-800 border border-gray-800 rounded-2xl flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-[11px] font-medium text-brand-400 capitalize">
                    {ex.primary_muscle_group}
                  </span>
                  <span className="text-[11px] text-gray-500 uppercase">{ex.equipment_required}</span>
                </div>
                <h3 className="text-base font-bold text-white mt-2">{ex.name}</h3>
                <div className="text-xs text-gray-400 mt-1">
                  Pattern: <span className="text-gray-300">{(ex.movement_pattern || '').replace('_', ' ')}</span>
                </div>
                {ex.instructions && <p className="text-xs text-gray-400 mt-2 leading-relaxed">{ex.instructions}</p>}
              </div>

              <button
                onClick={() => handleFindSubstitutes(ex.name)}
                className="w-full py-2 px-3 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-800 text-xs font-medium text-gray-300 flex items-center justify-center gap-1.5 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5 text-brand-400" />
                <span>Find Biomechanical Substitutes</span>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
