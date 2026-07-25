import React from 'react';
import type { Metadata, Viewport } from 'next';
import './globals.css';
import { AppShell } from '@/components/layout/AppShell';

export const metadata: Metadata = {
  title: {
    default: 'VFSTR ACSE Timetable Scheduler',
    template: '%s | VFSTR ACSE Timetable Scheduler',
  },
  description:
    'Automated Constraint-Solving Timetable Generation & Conflict Resolution Engine for Vignan University Department of ACSE.',
  keywords: [
    'VFSTR',
    'Timetable',
    'Scheduler',
    'Constraint Solver',
    'CP-SAT',
    'Genetic Algorithm',
    'ACSE Department',
  ],
  authors: [{ name: 'VFSTR ACSE Team' }],
  openGraph: {
    title: 'VFSTR ACSE Timetable Scheduler',
    description:
      'Automated Constraint-Solving Timetable Generation System for VFSTR University',
    type: 'website',
    locale: 'en_US',
    siteName: 'VFSTR ACSE Timetable Scheduler',
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#1E40AF' },
    { media: '(prefers-color-scheme: dark)', color: '#0F172A' },
  ],
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const theme = localStorage.getItem('vfstr-theme') || 'system';
                const supportDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (theme === 'dark' || (theme === 'system' && supportDark)) {
                  document.documentElement.setAttribute('data-theme', 'dark');
                  document.documentElement.classList.add('dark');
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
