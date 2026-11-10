const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface Goal {
  id?: string;
  primary_goal: string;
  target_weight_kg?: number;
  target_date?: string;
  sport_name?: string;
  sport_position?: string;
}

export interface AthleteProfile {
  id: string;
  user_id: string;
  age: number;
  sex: string;
  height_cm: number;
  current_weight_kg: number;
  timezone: string;
  training_experience_years: number;
  activity_level: string;
  occupation_type?: string;
  sport_name?: string;
  sport_position?: string;
  training_preferences: Record<string, any>;
  goals: Goal[];
}

export interface OnboardingPayload {
  age: number;
  sex: string;
  height_cm: number;
  current_weight_kg: number;
  timezone?: string;
  occupation_type?: string;
  activity_level: string;
  primary_goal: string;
  target_weight_kg?: number;
  target_date?: string;
  sport_name?: string;
  sport_position?: string;
  training_experience_years: number;
  days_per_week: number;
  preferred_days: string[];
  session_duration_minutes: number;
  available_equipment: string[];
  dietary_type: string;
  weekly_food_budget_inr: number;
  currency_code?: string;
  meals_per_day: number;
  staple_foods: string[];
  liked_foods: string[];
  disliked_foods: string[];
  allergies: string[];
  avoided_foods: string[];
}

class ApiClient {
  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  }

  public setToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  public removeToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'An unexpected error occurred' }));
      throw new Error(errorData.detail || `HTTP Error ${response.status}`);
    }

    return response.json();
  }

  // Auth Endpoints
  async register(data: { email: string; password: string; full_name: string }) {
    const res = await this.request<{ access_token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(res.access_token);
    return res;
  }

  async login(data: { email: string; password: string }) {
    const res = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe() {
    return this.request<User>('/auth/me');
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.removeToken();
    }
  }

  async deleteAccount() {
    const res = await this.request<{ message: string }>('/auth/me', { method: 'DELETE' });
    this.removeToken();
    return res;
  }

  // Athlete Profile & Onboarding Endpoints
  async getProfile() {
    return this.request<AthleteProfile>('/athlete/profile');
  }

  async createProfile(data: Partial<AthleteProfile> & { goal?: Goal }) {
    return this.request<AthleteProfile>('/athlete/profile', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProfile(data: Partial<AthleteProfile> & { goal?: Goal }) {
    return this.request<AthleteProfile>('/athlete/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async completeOnboarding(data: OnboardingPayload) {
    return this.request<any>('/athlete/onboarding', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getHydratedState() {
    return this.request<any>('/athlete/state');
  }

  async getWeightHistory() {
    return this.request<any>('/athlete/weight-history');
  }

  // Workout & Training Endpoints
  async listExercises(muscleGroup?: string, equipment?: string) {
    const params = new URLSearchParams();
    if (muscleGroup) params.set('muscle_group', muscleGroup);
    if (equipment) params.set('equipment', equipment);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return this.request<any[]>(`/training/exercises${qs}`);
  }

  async generateWorkoutPlan() {
    return this.request<any>('/training/generate-plan', { method: 'POST' });
  }

  async getActiveWorkoutPlan() {
    return this.request<any>('/training/active-plan');
  }

  async logWorkoutSession(data: {
    workout_day_id?: string;
    workout_name: string;
    session_rpe?: number;
    user_notes?: string;
    sets: Array<{
      exercise_name: string;
      set_number: number;
      weight_kg: number;
      reps_completed: number;
      actual_rpe?: number;
      is_warmup?: boolean;
    }>;
  }) {
    return this.request<any>('/training/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listWorkoutSessions() {
    return this.request<any[]>('/training/sessions');
  }

  async listPersonalRecords() {
    return this.request<any[]>('/training/prs');
  }

  async substituteExercise(exerciseName: string, availableEquipment: string[]) {
    return this.request<any>('/training/substitute', {
      method: 'POST',
      body: JSON.stringify({
        exercise_name: exerciseName,
        available_equipment: availableEquipment,
      }),
    });
  }

  // Nutrition & Food Endpoints
  async getNutritionTargets() {
    return this.request<any>('/nutrition/targets');
  }

  async listFoods(category?: string, vegetarianOnly?: boolean) {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (vegetarianOnly) params.set('vegetarian_only', 'true');
    const qs = params.toString() ? `?${params.toString()}` : '';
    return this.request<any[]>(`/nutrition/foods${qs}`);
  }

  async generateNutritionPlan() {
    return this.request<any>('/nutrition/generate-plan', { method: 'POST' });
  }

  async getActiveNutritionPlan() {
    return this.request<any>('/nutrition/active-plan');
  }

  async logFoodIntake(data: {
    food_item_id?: string;
    food_name: string;
    meal_type: string;
    preparation_state: string;
    quantity_grams: number;
    log_date?: string;
  }) {
    return this.request<any>('/nutrition/logs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getDailyFoodLogs(logDate?: string) {
    const qs = logDate ? `?log_date=${encodeURIComponent(logDate)}` : '';
    return this.request<any>(`/nutrition/logs${qs}`);
  }

  // AI Coach Orchestrator
  async askCoach(message: string, action: string = 'chat') {
    return this.request<any>('/coach/chat', {
      method: 'POST',
      body: JSON.stringify({ message, action }),
    });
  }

  async getAuditLogs() {
    return this.request<any[]>('/audit/logs');
  }

  // Progress, Check-ins, Body Analysis & Reminders
  async submitDailyCheckIn(data: {
    check_in_date?: string;
    weight_kg: number;
    energy_score: number;
    sleep_hours: number;
    sleep_quality_score: number;
    stress_score: number;
    soreness_score: number;
    hydration_liters: number;
    nutrition_adherence_percent: number;
    workout_completed: boolean;
    notes?: string;
  }) {
    return this.request<any>('/progress/check-ins', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listCheckIns() {
    return this.request<any>('/progress/check-ins');
  }

  async createBodyMeasurement(data: Record<string, any>) {
    return this.request<any>('/progress/measurements', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listBodyMeasurements() {
    return this.request<any[]>('/progress/measurements');
  }

  async getProgressAnalytics() {
    return this.request<any>('/progress/analytics');
  }

  async analyzeProgressPhoto(data: {
    photo_type: string;
    taken_at?: string;
    weight_at_capture_kg?: number;
    image_base64?: string;
    filename?: string;
  }) {
    return this.request<any>('/progress/photos/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listProgressPhotos() {
    return this.request<any[]>('/progress/photos');
  }

  async createReminder(data: {
    title: string;
    message?: string;
    notification_type: string;
    scheduled_time: string;
    days_of_week?: string[];
  }) {
    return this.request<any>('/progress/reminders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listReminders() {
    return this.request<any[]>('/progress/reminders');
  }

  async deleteReminder(id: string) {
    return this.request<any>(`/progress/reminders/${id}`, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();
