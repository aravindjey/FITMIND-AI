'use client';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { Activity, ShieldCheck, Database, Cpu, ArrowRight } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-dark-900 text-gray-100">
      <Navbar />

      {/* Hero Section */}
      <main className="flex-1 max-w-6xl mx-auto px-6 py-20 flex flex-col items-center justify-center text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-500 text-xs font-semibold uppercase tracking-wider mb-8">
          <Activity className="w-3.5 h-3.5" />
          <span>FITMIND AI • INTELLIGENT FITNESS. SCIENCE-DRIVEN RESULTS.</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold text-white tracking-tight leading-tight max-w-4xl mb-6">
          FITMIND AI <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-500 to-emerald-300">
            Intelligent Fitness. Science-Driven Results.
          </span>
        </h1>

        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mb-10 leading-relaxed">
          Not another ChatGPT wrapper. FitMind AI is a production-grade multi-agent athletic coaching platform combining deterministic sports-science math with persistent database state.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4">
          <Link
            href="/register"
            className="w-full sm:w-auto px-8 py-4 bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-xl transition-all shadow-xl shadow-brand-600/25 flex items-center justify-center gap-2 group"
          >
            <span>Create Athlete Account</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="/login"
            className="w-full sm:w-auto px-8 py-4 bg-gray-900 hover:bg-gray-800 border border-gray-800 text-gray-300 font-semibold rounded-xl transition-colors"
          >
            Sign In to Dashboard
          </Link>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid md:grid-cols-3 gap-6 w-full mt-24 text-left">
          <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl">
            <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500 mb-4">
              <Database className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Database Source of Truth</h3>
            <p className="text-sm text-gray-400">
              Athlete history, PRs, and check-ins are stored in PostgreSQL. We never rely on transient LLM memory.
            </p>
          </div>

          <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl">
            <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500 mb-4">
              <Cpu className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Deterministic Math Core</h3>
            <p className="text-sm text-gray-400">
              BMR, TDEE, 1RM progression, and weight trends are calculated with pure reproducible math engines.
            </p>
          </div>

          <div className="p-6 bg-dark-800 border border-gray-800 rounded-2xl">
            <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500 mb-4">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Safety Guardrails Engine</h3>
            <p className="text-sm text-gray-400">
              Configurable safety rules and validation engines audit all AI recommendations before they touch your profile.
            </p>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-800 py-6 text-center text-xs text-gray-500">
        FITMIND AI &copy; 2026 — INTELLIGENT FITNESS. SCIENCE-DRIVEN RESULTS. Built with Next.js, FastAPI &amp; PostgreSQL.
      </footer>
    </div>
  );
}
