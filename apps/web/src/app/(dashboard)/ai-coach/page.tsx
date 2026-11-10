'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Bot, Send, Sparkles, Database, ShieldCheck, Cpu } from 'lucide-react';

interface ChatTurn {
  role: 'user' | 'coach';
  message: string;
  targetSpokes?: string[];
  referencedMetrics?: string[];
  actionableSteps?: string[];
  isFallback?: boolean;
}

export default function AICoachPage() {
  const [state, setState] = useState<any | null>(null);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [turns, setTurns] = useState<ChatTurn[]>([
    {
      role: 'coach',
      message:
        'Welcome to your FITMIND AI Hub-and-Spoke Coaching Console — Intelligent Fitness, Science-Driven Results. Every response I generate is grounded directly in your authoritative PostgreSQL/SQLite athlete state: your current weight, 7-day EMA trend, active workout split, INR food budget, and recovery readiness score.',
      targetSpokes: ['CoachOrchestrator', 'AthleteStateHydrator'],
      referencedMetrics: ['Database-Backed Context Active'],
    },
  ]);

  useEffect(() => {
    apiClient
      .getHydratedState()
      .then((res) => setState(res))
      .catch(() => setState(null));
  }, []);

  const handleSend = async (promptText?: string) => {
    const query = (promptText ?? input).trim();
    if (!query || sending) return;
    setInput('');
    setSending(true);
    setTurns((prev) => [...prev, { role: 'user', message: query }]);

    try {
      const res = await apiClient.askCoach(query, 'chat');
      setTurns((prev) => [
        ...prev,
        {
          role: 'coach',
          message: res.answer || res.reply,
          targetSpokes: res.target_spokes || ['FitnessCoachingAgent'],
          referencedMetrics: res.referenced_metrics || res.referenced_database_metrics || [],
          actionableSteps: res.actionable_steps || res.actionable_next_steps || [],
          isFallback: res.is_fallback,
        },
      ]);
    } catch (err: any) {
      setTurns((prev) => [
        ...prev,
        {
          role: 'coach',
          message: err.message || 'Unable to reach AI Coach endpoint.',
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const quickPrompts = [
    'Review my current weight trend, calorie targets, and active workout split.',
    'My sleep was low last night and soreness is high. How should I adjust today’s workout load?',
    'Suggest high-protein Indian meals within my weekly ₹ INR budget.',
    'How does double progression work on my compound lifts?',
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">FITMIND AI Coach &amp; Multi-Agent Orchestrator</h1>
          <p className="text-sm text-gray-400">
            Intelligent Fitness. Science-Driven Results. • Zero-hallucination coaching hydrated from authoritative database records
          </p>
        </div>
        {state?.has_profile && (
          <div className="px-3.5 py-2 rounded-xl bg-dark-800 border border-gray-800 flex items-center gap-2 text-xs text-gray-300">
            <Database className="w-4 h-4 text-brand-400" />
            <span>
              Hydrated: {state.athlete_summary?.weight_kg} kg • {state.nutrition_targets?.target_calories} kcal
            </span>
          </div>
        )}
      </div>

      {/* Quick Prompt Chips */}
      <div className="flex flex-wrap gap-2">
        {quickPrompts.map((q, i) => (
          <button
            key={i}
            onClick={() => handleSend(q)}
            disabled={sending}
            className="px-3.5 py-2 rounded-xl bg-dark-800 hover:bg-gray-800 border border-gray-800 text-xs text-gray-300 transition-colors text-left"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Conversation Area */}
      <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4 min-h-[420px] max-h-[560px] overflow-y-auto">
        {turns.map((turn, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${turn.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-2xl rounded-2xl p-4 space-y-3 ${
                turn.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-900 border border-gray-800 text-gray-200'
              }`}
            >
              {turn.role === 'coach' && (
                <div className="flex flex-wrap items-center gap-2 text-[11px]">
                  <span className="px-2 py-0.5 rounded-md bg-brand-500/15 text-brand-400 font-semibold flex items-center gap-1">
                    <Bot className="w-3 h-3" />
                    CoachOrchestrator
                  </span>
                  {turn.targetSpokes?.map((spoke, sIdx) => (
                    <span
                      key={sIdx}
                      className="px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-300 font-medium"
                    >
                      {spoke}
                    </span>
                  ))}
                  {turn.isFallback !== undefined && (
                    <span className="px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-300 flex items-center gap-1">
                      <Cpu className="w-3 h-3" />
                      {turn.isFallback ? 'Deterministic Fallback Engine' : 'Live LLM Provider'}
                    </span>
                  )}
                </div>
              )}

              <p className="text-sm leading-relaxed whitespace-pre-line">{turn.message}</p>

              {turn.actionableSteps && turn.actionableSteps.length > 0 && (
                <div className="pt-2 border-t border-gray-800 space-y-1">
                  <div className="text-[11px] font-semibold uppercase text-brand-400">
                    Actionable Next Steps
                  </div>
                  <ul className="list-disc list-inside text-xs text-gray-300 space-y-1">
                    {turn.actionableSteps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}

              {turn.referencedMetrics && turn.referencedMetrics.length > 0 && (
                <div className="pt-2 flex flex-wrap gap-1.5">
                  {turn.referencedMetrics.map((m, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded bg-gray-800 text-[11px] text-gray-400 flex items-center gap-1"
                    >
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      {m}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div className="text-xs text-gray-400 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-400 animate-spin" />
            <span>Hydrating athlete database state & consulting specialist agents...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask your AI Coach about training load, macros, recovery, or Indian staple meals..."
          className="flex-1 px-4 py-3 bg-dark-800 border border-gray-800 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="px-6 py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
}
