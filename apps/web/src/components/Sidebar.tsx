'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  User,
  ClipboardCheck,
  Dumbbell,
  BookOpen,
  Utensils,
  TrendingUp,
  Camera,
  HeartPulse,
  Bell,
  Bot,
  Settings,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Onboarding Wizard', href: '/onboarding', icon: ClipboardCheck },
  { name: 'Athlete Profile', href: '/profile', icon: User },
  { name: 'AI Fitness Coach', href: '/ai-coach', icon: Bot },
  { name: 'Workout Planner & Logger', href: '/workout', icon: Dumbbell },
  { name: 'Exercise Library', href: '/exercises', icon: BookOpen },
  { name: 'Nutrition & Food Tracker', href: '/nutrition', icon: Utensils },
  { name: 'Progress Analytics', href: '/progress', icon: TrendingUp },
  { name: 'Daily Check-In & Recovery', href: '/check-in', icon: HeartPulse },
  { name: 'Body Photo Analysis', href: '/body-analysis', icon: Camera },
  { name: 'Reminders & Schedule', href: '/reminders', icon: Bell },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-gray-800 bg-dark-800 min-h-[calc(100vh-73px)] p-4 flex flex-col justify-between shrink-0">
      <div className="space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

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
              <Icon className="w-4 h-4 shrink-0" />
              <span className="truncate">{item.name}</span>
            </Link>
          );
        })}
      </div>

      <div className="p-3 bg-gray-900/60 border border-gray-800/80 rounded-xl text-xs text-gray-400 space-y-1 mt-6">
        <div className="font-semibold text-gray-300">Authoritative State Engine</div>
        <div>8 AI Specialists Active</div>
        <div className="text-brand-500">INR (₹) & Validated Macros</div>
      </div>
    </aside>
  );
}
