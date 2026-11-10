import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'FITMIND AI | Intelligent Fitness. Science-Driven Results.',
    template: '%s | FITMIND AI',
  },
  description:
    'FITMIND AI — Intelligent Fitness. Science-Driven Results. Production-grade personalized fitness and athletic coaching platform powered by deterministic sports science and persistent database state.',
  applicationName: 'FITMIND AI',
  openGraph: {
    title: 'FITMIND AI | Intelligent Fitness. Science-Driven Results.',
    description:
      'Persistent multi-agent athletic coaching platform combining deterministic BMR/TDEE/1RM math engines with authoritative athlete state.',
    siteName: 'FITMIND AI',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'FITMIND AI | Intelligent Fitness. Science-Driven Results.',
    description:
      'Intelligent Fitness. Science-Driven Results. Authoritative state and deterministic sports-science coaching.',
  },
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
