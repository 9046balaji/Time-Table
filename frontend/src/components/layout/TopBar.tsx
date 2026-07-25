'use client';

import React from 'react';
import { Sparkles, PanelLeftClose, PanelLeftOpen, Sun, Moon, Search, HelpCircle, Menu } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

interface TopBarProps {
  isSidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
  onOpenCommandPalette?: () => void;
  onOpenHelp?: () => void;
  onToggleMobileMenu?: () => void;
}

export function TopBar({
  isSidebarCollapsed = false,
  onToggleSidebar,
  onOpenCommandPalette,
  onOpenHelp,
  onToggleMobileMenu,
}: TopBarProps) {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 flex items-center justify-between transition-colors print:hidden">
      <div className="flex items-center gap-3">
        {/* Mobile drawer toggle */}
        <button
          onClick={onToggleMobileMenu}
          className="p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg md:hidden cursor-pointer"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Desktop Sidebar toggle */}
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="hidden md:flex p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            title={isSidebarCollapsed ? "Expand Navigation Sidebar" : "Collapse Navigation Sidebar"}
          >
            {isSidebarCollapsed ? (
              <PanelLeftOpen className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <PanelLeftClose className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            )}
          </button>
        )}

        <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 truncate">
          Department of ACSE Timetable Management
        </h2>
        <span className="hidden lg:inline-block px-2.5 py-1 bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 text-xs font-semibold rounded-full border border-blue-200 dark:border-blue-800/60">
          Semester I • 44 Sections
        </span>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* Command Palette Trigger */}
        <button
          onClick={onOpenCommandPalette}
          className="hidden sm:flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/80 hover:bg-slate-200 dark:hover:bg-slate-700/80 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
          title="Search & Quick Actions (Ctrl + K)"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Quick Search...</span>
          <kbd className="px-1.5 py-0.5 font-mono text-[10px] bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded text-slate-600 dark:text-slate-300">
            Ctrl+K
          </kbd>
        </button>

        {/* Engine Ready Badge */}
        <div className="hidden xl:flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
          <Sparkles className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
          <span>CP-SAT Engine Ready</span>
        </div>

        {/* Theme Switcher */}
        <button
          onClick={toggleTheme}
          className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          title={`Switch to ${resolvedTheme === 'dark' ? 'Light' : 'Dark'} Mode`}
        >
          {resolvedTheme === 'dark' ? (
            <Sun className="w-5 h-5 text-amber-400" />
          ) : (
            <Moon className="w-5 h-5 text-slate-600" />
          )}
        </button>

        {/* Help Modal Trigger */}
        <button
          onClick={onOpenHelp}
          className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          title="Help & Shortcuts (?)"
        >
          <HelpCircle className="w-5 h-5" />
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-2 border-l border-slate-200 dark:border-slate-800 pl-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
            AC
          </div>
          <div className="text-xs hidden md:block">
            <div className="font-semibold text-slate-900 dark:text-slate-100">Coordinator</div>
            <div className="text-slate-500 dark:text-slate-400 text-[10px]">ACSE Dept</div>
          </div>
        </div>
      </div>
    </header>
  );
}
