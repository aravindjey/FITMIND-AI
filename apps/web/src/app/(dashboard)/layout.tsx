'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import Sidebar from '@/components/Sidebar';
import { apiClient, User } from '@/lib/api-client';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .getMe()
      .then((userData) => {
        setUser(userData);
      })
      .catch(() => {
        router.push('/login');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center text-gray-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          <span>Authenticating Session...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-dark-900 text-gray-100">
      <Navbar user={user} />
      <div className="flex flex-1">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-y-auto">
          <main className="flex-1 p-8 max-w-7xl w-full">{children}</main>
          <footer className="border-t border-gray-800/80 px-8 py-4 text-xs text-gray-500 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span className="font-semibold text-gray-400">FITMIND AI &copy; 2026</span>
            <span className="text-brand-500 font-semibold tracking-wider uppercase text-[11px]">
              INTELLIGENT FITNESS. SCIENCE-DRIVEN RESULTS.
            </span>
          </footer>
        </div>
      </div>
    </div>
  );
}
