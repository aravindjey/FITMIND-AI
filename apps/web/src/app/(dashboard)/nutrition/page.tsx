'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import {
  Utensils,
  Sparkles,
  CheckCircle,
  AlertCircle,
  Plus,
} from 'lucide-react';

export default function NutritionPage() {
  const [targetsData, setTargetsData] = useState<any | null>(null);
  const [plan, setPlan] = useState<any | null>(null);
  const [foods, setFoods] = useState<any[]>([]);
  const [dailyLogs, setDailyLogs] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loggingFood, setLoggingFood] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [foodForm, setFoodForm] = useState({
    food_name: 'Whole Wheat Roti / Chapati (Cooked)',
    meal_type: 'lunch',
    preparation_state: 'cooked',
    quantity_grams: 150,
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [tRes, pRes, fRes, lRes] = await Promise.all([
        apiClient.getNutritionTargets().catch(() => null),
        apiClient.getActiveNutritionPlan().catch(() => null),
        apiClient.listFoods().catch(() => []),
        apiClient.getDailyFoodLogs().catch(() => null),
      ]);
      setTargetsData(tRes);
      if (pRes?.has_active_plan) {
        setPlan(pRes.plan);
      }
      setFoods(fRes || []);
      if (fRes?.length > 0) {
        setFoodForm((prev) => ({
          ...prev,
          food_name: fRes.some((f: any) => f.name === prev.food_name) ? prev.food_name : fRes[0].name,
        }));
      }
      setDailyLogs(lRes);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerateNutritionPlan = async () => {
    setGenerating(true);
    setError(null);
    setMessage(null);
    try {
      const res = await apiClient.generateNutritionPlan();
      setMessage(
        `Generated meal plan "${res.plan.name}" • Est. Daily Cost: ₹${res.plan.estimated_daily_cost_inr} INR`
      );
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to generate nutrition plan. Complete onboarding first.');
    } finally {
      setGenerating(false);
    }
  };

  const handleLogFood = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoggingFood(true);
    setError(null);
    setMessage(null);
    try {
      const selectedFood = foods.find((f) => f.name === foodForm.food_name);
      const res = await apiClient.logFoodIntake({
        food_item_id: selectedFood?.id,
        food_name: foodForm.food_name,
        meal_type: foodForm.meal_type,
        preparation_state: foodForm.preparation_state,
        quantity_grams: Number(foodForm.quantity_grams),
      });
      setMessage(
        `Logged ${res.quantity_grams}g (${res.preparation_state}) ${res.food_name} • +${res.calories} kcal (${res.protein_g}g protein)`
      );
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to log food intake');
    } finally {
      setLoggingFood(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-400">Loading Nutrition Engine & Indian Staple Database...</div>;
  }

  const targets = targetsData;
  const totals = dailyLogs?.totals || { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">FITMIND AI Nutrition Planner &amp; Food Tracker</h1>
          <p className="text-sm text-gray-400">
            Intelligent Fitness. Science-Driven Results. • Mifflin-St Jeor deterministic targets, Indian staple meal synthesis, and raw/cooked gram logging
          </p>
        </div>
        <button
          onClick={handleGenerateNutritionPlan}
          disabled={generating}
          className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl flex items-center gap-2 self-start"
        >
          <Sparkles className="w-4 h-4" />
          <span>{generating ? 'Synthesizing Meal Plan...' : plan ? 'Regenerate Meal Plan' : 'Generate AI Meal Plan'}</span>
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

      {targets?.goal_conflict_warning && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-amber-200 block mb-0.5">
              Goal &amp; Target Weight Conflict Adjusted ({targets.effective_regime === 'recomposition_cut' ? 'Recomposition Deficit -15%' : 'Conflict Detected'})
            </span>
            <span>{targets.goal_conflict_warning}</span>
          </div>
        </div>
      )}

      {/* Deterministic Metabolic & Macro Targets */}
      {targets && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="p-4 bg-dark-800 border border-gray-800 rounded-2xl">
            <div className="text-[11px] font-semibold uppercase text-gray-400">BMR / TDEE</div>
            <div className="text-lg font-bold text-white mt-1">
              {targets.bmr_kcal} / {targets.tdee_kcal} <span className="text-xs font-normal text-gray-400">kcal</span>
            </div>
            <div className="text-[11px] text-gray-500 mt-0.5">Mifflin-St Jeor</div>
          </div>

          <div className="p-4 bg-dark-800 border border-gray-800 rounded-2xl">
            <div className="text-[11px] font-semibold uppercase text-gray-400">Daily Target</div>
            <div className="text-lg font-bold text-brand-400 mt-1">
              {targets.target_calories} <span className="text-xs font-normal text-gray-400">kcal</span>
            </div>
            <div className="text-[11px] text-gray-500 mt-0.5">
              {typeof targets.calorie_adjustment_percent === 'number'
                ? `${targets.calorie_adjustment_percent > 0 ? '+' : ''}${targets.calorie_adjustment_percent}% vs TDEE • `
                : ''}
              Logged: {totals.calories} kcal
            </div>
          </div>

          <div className="p-4 bg-dark-800 border border-gray-800 rounded-2xl">
            <div className="text-[11px] font-semibold uppercase text-gray-400">Protein Target</div>
            <div className="text-lg font-bold text-emerald-400 mt-1">{targets.protein_grams} g</div>
            <div className="text-[11px] text-gray-500 mt-0.5">Logged Today: {totals.protein_g} g</div>
          </div>

          <div className="p-4 bg-dark-800 border border-gray-800 rounded-2xl">
            <div className="text-[11px] font-semibold uppercase text-gray-400">Carbs & Fats</div>
            <div className="text-lg font-bold text-white mt-1">
              {targets.carbs_grams}g C / {targets.fat_grams}g F
            </div>
            <div className="text-[11px] text-gray-500 mt-0.5">
              Fiber: {targets.fiber_grams}g • Water: {targets.hydration_liters}L
            </div>
          </div>

          <div className="p-4 bg-dark-800 border border-gray-800 rounded-2xl">
            <div className="text-[11px] font-semibold uppercase text-gray-400">Weekly Food Budget</div>
            <div className="text-lg font-bold text-amber-400 mt-1">
              ₹{targets.weekly_food_budget_inr || 2500} <span className="text-xs font-normal text-gray-400">INR</span>
            </div>
            <div className="text-[11px] text-gray-500 mt-0.5 capitalize">
              Diet: {(targets.dietary_type || 'omnivore').replace('_', ' ')}
            </div>
          </div>
        </div>
      )}

      {/* Active Meal Plan */}
      {plan ? (
        <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-gray-800 pb-4">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-brand-400">
                Active Constraint-Aware Meal Plan
              </span>
              <h2 className="text-xl font-bold text-white mt-0.5">{plan.name}</h2>
              {plan.calculation_assumptions && (
                <p className="text-xs text-gray-400 mt-1">{plan.calculation_assumptions}</p>
              )}
            </div>
            <div className="text-right">
              <div className="text-sm font-bold text-emerald-400">
                Est. Daily Cost: ₹{plan.estimated_daily_cost_inr} INR (~₹
                {Math.round((plan.estimated_daily_cost_inr || 0) * 7)}/wk)
              </div>
              <div className="text-xs text-gray-400">
                Target: {plan.daily_calories} kcal • {plan.protein_grams}g P • {plan.carbs_grams}g C • {plan.fat_grams}g F
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">
                Meals Sum:{' '}
                {plan.actual_calories ??
                  plan.meals?.reduce((sum: number, m: any) => sum + Number(m.target_calories || 0), 0)}{' '}
                kcal •{' '}
                {plan.actual_protein_g ??
                  Math.round(
                    (plan.meals?.reduce((sum: number, m: any) => sum + Number(m.protein_g || 0), 0) || 0) * 10
                  ) / 10}
                g P •{' '}
                {plan.actual_carbs_g ??
                  Math.round(
                    (plan.meals?.reduce((sum: number, m: any) => sum + Number(m.carbs_g || 0), 0) || 0) * 10
                  ) / 10}
                g C •{' '}
                {plan.actual_fat_g ??
                  Math.round(
                    (plan.meals?.reduce((sum: number, m: any) => sum + Number(m.fat_g || 0), 0) || 0) * 10
                  ) / 10}
                g F
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {plan.meals?.map((meal: any, idx: number) => (
              <div key={meal.id || idx} className="p-4 rounded-xl bg-gray-900 border border-gray-800 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-semibold uppercase text-brand-400">
                      Meal {meal.meal_number} ({meal.time_of_day})
                    </span>
                    <h4 className="font-bold text-white text-sm">{meal.name}</h4>
                  </div>
                  <div className="text-xs font-semibold text-white">{meal.target_calories} kcal</div>
                </div>
                <div className="text-xs text-gray-400">
                  P: <span className="text-emerald-400">{meal.protein_g}g</span> • C:{' '}
                  <span className="text-blue-400">{meal.carbs_g}g</span> • F:{' '}
                  <span className="text-amber-400">{meal.fat_g}g</span> • Cost: ₹{meal.estimated_cost_inr}
                </div>
                <div className="space-y-1 pt-1 border-t border-gray-800/80">
                  {meal.ingredients?.map((item: any, i: number) => (
                    <div key={i} className="flex justify-between text-xs text-gray-300">
                      <span>
                        {item.name} ({item.preparation_state})
                      </span>
                      <span className="text-gray-400">
                        {item.quantity_grams}g • {item.calories} kcal
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-8 bg-dark-800 border border-gray-800 rounded-2xl text-center space-y-3">
          <Utensils className="w-10 h-10 text-brand-500 mx-auto" />
          <h3 className="text-lg font-bold text-white">No Active Nutrition Plan Yet</h3>
          <p className="text-xs text-gray-400 max-w-md mx-auto">
            Click &ldquo;Generate AI Meal Plan&rdquo; above to synthesize an Indian staple meal strategy matched to your
            caloric targets, dietary restrictions, and ₹ INR budget.
          </p>
        </div>
      )}

      {/* Daily Food Logger & Today's Logs */}
      <div className="grid lg:grid-cols-2 gap-6">
        <form onSubmit={handleLogFood} className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3">
            Log Daily Food Intake (Raw vs. Cooked Precision)
          </h3>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
              Select Validated Food Item
            </label>
            <select
              value={foodForm.food_name}
              onChange={(e) => setFoodForm({ ...foodForm, food_name: e.target.value })}
              className="w-full px-3.5 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
            >
              {foods.map((f) => (
                <option key={f.id} value={f.name}>
                  {f.name} ({f.calories_per_100g} kcal, {f.protein_per_100g}g P per 100g {f.preparation_state})
                </option>
              ))}
            </select>
          </div>

          <div className="grid sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Meal Type</label>
              <select
                value={foodForm.meal_type}
                onChange={(e) => setFoodForm({ ...foodForm, meal_type: e.target.value })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-xs"
              >
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="snack">Evening Snack</option>
                <option value="dinner">Dinner</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Prep State</label>
              <select
                value={foodForm.preparation_state}
                onChange={(e) => setFoodForm({ ...foodForm, preparation_state: e.target.value })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-xs"
              >
                <option value="cooked">Cooked Weight</option>
                <option value="raw">Raw / Uncooked</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Quantity (grams)</label>
              <input
                type="number"
                min={10}
                max={2000}
                value={foodForm.quantity_grams}
                onChange={(e) => setFoodForm({ ...foodForm, quantity_grams: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-xs"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loggingFood}
            className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>{loggingFood ? 'Logging Food...' : 'Log Food Entry'}</span>
          </button>
        </form>

        <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <h3 className="text-lg font-bold text-white">Today&apos;s Logged Intake</h3>
            <span className="text-xs font-semibold text-brand-400">
              {totals.calories} kcal • {totals.protein_g}g P
            </span>
          </div>

          {dailyLogs?.logs?.length > 0 ? (
            <div className="space-y-2.5 max-h-72 overflow-y-auto">
              {dailyLogs.logs.map((log: any) => (
                <div
                  key={log.id}
                  className="p-3 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-semibold text-white">{log.food_name}</div>
                    <div className="text-gray-400 capitalize">
                      {log.meal_type} • {log.quantity_grams}g ({log.preparation_state})
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-white">{log.calories} kcal</div>
                    <div className="text-emerald-400">
                      {log.protein_g}g P • {log.carbs_g}g C • {log.fat_g}g F
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-400 py-8 text-center">
              No food entries logged today. Select a food item on the left to track your daily macros.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
