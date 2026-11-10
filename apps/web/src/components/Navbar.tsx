'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { Activity, LogOut, User as UserIcon } from 'lucide-react';

interface NavbarProps {
  user?: { full_name: string; email: string } | null;
}

export default function Navbar({ user }: NavbarProps) {
  const router = useRouter();

  const handleLogout = async () => {
    await apiClient.logout();
    router.push('/login');
  };

  return (
    <nav className="border-b border-gray-800 bg-dark-800/80 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-50">
      <Link href="/" className="flex items-center gap-3 group">
        <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-500 group-hover:scale-105 transition-transform">
          <Activity className="w-6 h-6" />
        </div>
        <div>
          <span className="font-bold text-lg text-white tracking-tight">FITMIND AI</span>
          <span className="block text-[10px] text-brand-500 font-semibold tracking-wider uppercase">
            INTELLIGENT FITNESS. SCIENCE-DRIVEN RESULTS.
          </span>
        </div>
      </Link>

      <div className="flex items-center gap-4">
        {user ? (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800 text-sm">
              <UserIcon className="w-4 h-4 text-brand-500" />
              <span className="text-gray-200 font-medium">{user.full_name}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-500 rounded-lg transition-colors shadow-lg shadow-brand-600/20"
            >
              Get Started
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
