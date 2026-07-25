'use client';

import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function AppShell({ children }: { children: React.ReactNode }) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const toggleSidebar = () => setIsSidebarCollapsed((prev) => !prev);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar isCollapsed={isSidebarCollapsed} onToggle={toggleSidebar} />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar isSidebarCollapsed={isSidebarCollapsed} onToggleSidebar={toggleSidebar} />
        <main className="p-6 flex-1">{children}</main>
      </div>
    </div>
  );
}
