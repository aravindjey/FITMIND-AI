import Link from 'next/link';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  actionHref?: string;
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  actionText,
  actionHref,
}: EmptyStateProps) {
  return (
    <div className="border border-dashed border-gray-800 bg-gray-900/30 rounded-2xl p-10 flex flex-col items-center justify-center text-center max-w-md mx-auto my-8">
      <div className="w-12 h-12 rounded-xl bg-gray-800/80 border border-gray-700 flex items-center justify-center text-gray-400 mb-4">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 mb-6">{description}</p>
      {actionText && actionHref && (
        <Link
          href={actionHref}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold rounded-lg transition-colors shadow-lg shadow-brand-600/20"
        >
          {actionText}
        </Link>
      )}
    </div>
  );
}
