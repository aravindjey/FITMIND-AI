'use client';
import { useEffect, useState } from 'react';
import { apiClient, User } from '@/lib/api-client';
import { Settings as SettingsIcon, Shield, Database, Bell, Cpu } from 'lucide-react';

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  useEffect(() => {
    apiClient.getMe().then((data) => setUser(data)).catch(() => {});
    apiClient.getAuditLogs().then((logs) => setAuditLogs(logs || [])).catch(() => {});
  }, []);

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white">FITMIND AI Account, Security &amp; Audit Settings</h1>
        <p className="text-sm text-gray-400">
          Intelligent Fitness. Science-Driven Results. • Manage security, tenant isolation rules, currency preferences, and inspect AI execution audit trails
        </p>
      </div>

      <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-gray-800">
          <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-white">Account Identity</h3>
            <p className="text-sm text-gray-400">
              {user?.full_name} ({user?.email})
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-900/50 border border-gray-800 rounded-xl">
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-brand-500" />
              <div>
                <div className="text-sm font-semibold text-white">Tenant Data Isolation</div>
                <div className="text-xs text-gray-400">Strict user_id ownership checks active on all 21 database tables</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 text-xs font-semibold">
              Enforced
            </span>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-900/50 border border-gray-800 rounded-xl">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-brand-500" />
              <div>
                <div className="text-sm font-semibold text-white">Default Currency Context</div>
                <div className="text-xs text-gray-400">Indian Rupee (₹ INR) primary budget calculation context</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-md bg-brand-500/10 text-brand-500 text-xs font-semibold">
              INR (₹)
            </span>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-900/50 border border-gray-800 rounded-xl">
            <div className="flex items-center gap-3">
              <SettingsIcon className="w-5 h-5 text-brand-500" />
              <div>
                <div className="text-sm font-semibold text-white">AI Provider Mode</div>
                <div className="text-xs text-gray-400">
                  Provider-independent LLM & Vision abstraction with deterministic fallback
                </div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-md bg-gray-800 text-gray-300 text-xs font-semibold">
              Configurable via Env
            </span>
          </div>
        </div>
      </div>

      {/* AI Agent Execution Audit Log */}
      <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-gray-800 pb-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-brand-400" />
            <h3 className="font-bold text-white">AI Agent Execution Audit Log ({auditLogs.length})</h3>
          </div>
          <span className="text-xs text-gray-400">Persisted in agent_audit_logs</span>
        </div>

        {auditLogs.length > 0 ? (
          <div className="space-y-2.5 max-h-80 overflow-y-auto">
            {auditLogs.map((log) => (
              <div
                key={log.id}
                className="p-3.5 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-white">
                    {log.agent_name} <span className="text-gray-400 font-normal">({log.action})</span>
                  </div>
                  <div className="text-gray-400">
                    {log.output_snapshot?.is_fallback ? 'Deterministic Fallback Engine' : 'Live Provider'} •{' '}
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="text-right">
                  <span
                    className={`px-2 py-0.5 rounded font-semibold ${
                      log.validation_passed
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : 'bg-red-500/10 text-red-400'
                    }`}
                  >
                    {log.validation_passed ? 'Validated' : 'Rejected'}
                  </span>
                  <div className="text-gray-500 mt-0.5">{log.execution_time_ms} ms</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400 py-4 text-center">
            No AI agent runs recorded yet. Generate a plan or chat with the AI Coach to populate audit logs.
          </p>
        )}
      </div>
    </div>
  );
}
