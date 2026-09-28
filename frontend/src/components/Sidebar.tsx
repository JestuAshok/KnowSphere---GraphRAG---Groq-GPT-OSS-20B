import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Home, MessageSquare, Share2, FileText, BarChart2,
  Users, Settings, LogOut, Sparkles
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/dashboard', icon: Home, label: 'Home' },
  { to: '/ask', icon: MessageSquare, label: 'Ask' },
  { to: '/graph', icon: Share2, label: 'Knowledge Graph' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/insights', icon: BarChart2, label: 'Insights' },
  { to: '/teams', icon: Users, label: 'Teams' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('ks_user') || '{"name":"User"}');

  const handleLogout = () => {
    localStorage.removeItem('ks_token');
    localStorage.removeItem('ks_user');
    navigate('/');
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="px-4 mb-6 flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
          <Sparkles size={16} className="text-white" />
        </div>
        <span className="text-white font-bold text-base tracking-tight">KnowSphere</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 px-2">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className={({ isActive }) =>
            `nav-item ${isActive ? 'active' : ''}`
          }>
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-2 mt-4 border-t border-white/10 pt-4">
        <div className="flex items-center gap-3 px-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-xs font-bold">
            {user.name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-xs font-semibold truncate">{user.name}</p>
            <p className="text-[#A0A0C8] text-xs truncate">{user.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="nav-item w-full text-left mt-1 text-red-400 hover:bg-red-900/20 hover:text-red-300"
        >
          <LogOut size={16} />
          <span>Log out</span>
        </button>
      </div>
    </aside>
  );
};
