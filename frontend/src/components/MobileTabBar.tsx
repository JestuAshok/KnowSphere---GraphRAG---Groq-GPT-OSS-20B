import React from 'react';
import { Home, MessageSquare, Share2, FileText } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const TABS = [
  { to: '/dashboard', icon: Home, label: 'Home' },
  { to: '/ask', icon: MessageSquare, label: 'Ask' },
  { to: '/graph', icon: Share2, label: 'Graph' },
  { to: '/documents', icon: FileText, label: 'Docs' },
];

export const MobileTabBar: React.FC = () => (
  <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 md:hidden">
    <div className="flex">
      {TABS.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center py-3 gap-1 text-xs font-medium transition-colors
             ${isActive ? 'text-brand-600' : 'text-gray-400'}`
          }
        >
          <Icon size={20} />
          {label}
        </NavLink>
      ))}
    </div>
  </nav>
);
