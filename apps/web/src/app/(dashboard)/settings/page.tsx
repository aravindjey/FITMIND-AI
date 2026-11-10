'use client';
import { useEffect, useState } from 'react';
import { apiClient, User } from '@/lib/api-client';
import { Settings as SettingsIcon, Shield, Database, Bell } from 'lucide-react';

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    apiClient.getMe().then((data) => setUser(data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Account & System Settings</h1>
        <p className="text-sm text-gray-400">Manage security, isolation rules, and currency preferences</p>
      </div>

      <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-gray-800">
          <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-white">Account Identity</h3>
            <p className="text-sm text-gray-400">{user?.full_name} ({user?.email})</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-900/50 border border-gray-800 rounded-xl">
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-brand-500" />
              <div>
                <div className="text-sm font-semibold text-white">Tenant Data Isolation</div>
                <div className="text-xs text-gray-400">Strict ownership checks active on all database routes</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 text-xs font-semibold">Enforced</span>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-900/50 border border-gray-800 rounded-xl">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-brand-500" />
              <div>
                <div className="text-sm font-semibold text-white">Default Currency Context</div>
                <div className="text-xs text-gray-400">Primary development & testing currency context</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-md bg-brand-500/10 text-brand-500 text-xs font-semibold">INR (₹)</span>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-900/50 border border-gray-800 rounded-xl">
            <div className="flex items-center gap-3">
              <SettingsIcon className="w-5 h-5 text-brand-500" />
              <div>
                <div className="text-sm font-semibold text-white">AI Provider Mode</div>
                <div className="text-xs text-gray-400">Provider-independent LLM & Vision abstraction</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-md bg-gray-800 text-gray-300 text-xs font-semibold">Configurable via Env</span>
          </div>
        </div>
      </div>
    </div>
  );
}
