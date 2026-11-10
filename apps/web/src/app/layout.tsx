import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Fitness Coach | Persistent Athletic Coaching Platform',
  description: 'Production-Grade Personalized Fitness & Athletic Coaching Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-dark-900 text-gray-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
