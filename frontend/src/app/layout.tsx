import React from 'react';
import './globals.css';
import { AppShell } from '@/components/layout/AppShell';

export const metadata = {
  title: 'VFSTR ACSE Timetable Scheduler',
  description: 'Automated Constraint-Solving Timetable Generation System for VFSTR University',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
