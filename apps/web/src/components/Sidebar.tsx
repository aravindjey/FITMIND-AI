'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, User, Dumbbell, Utensils, TrendingUp, Settings, Bot } from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Athlete Profile', href: '/profile', icon: User },
  { name: 'Training (Phase 3)', href: '#', icon: Dumbbell, disabled: true },
  { name: 'Nutrition (Phase 3)', href: '#', icon: Utensils, disabled: true },
  { name: 'Progress (Phase 4)', href: '#', icon: TrendingUp, disabled: true },
  { name: 'AI Coach (Phase 3)', href: '#', icon: Bot, disabled: true },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-gray-800 bg-dark-800 min-h-[calc(100vh-73px)] p-4 flex flex-col justify-between">
      <div className="space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          if (item.disabled) {
            return (
              <div
                key={item.name}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-600 cursor-not-allowed select-none"
              >
                <Icon className="w-5 h-5 opacity-40" />
                <span>{item.name}</span>
              </div>
            );
          }

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-500/10 text-brand-500 border border-brand-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </div>

      <div className="p-3 bg-gray-900/60 border border-gray-800/80 rounded-xl text-xs text-gray-400 space-y-1">
        <div className="font-semibold text-gray-300">Phase 1 Foundation</div>
        <div>System Version: 1.0.0</div>
        <div className="text-brand-500">Persistent State Active</div>
      </div>
    </aside>
  );
}
