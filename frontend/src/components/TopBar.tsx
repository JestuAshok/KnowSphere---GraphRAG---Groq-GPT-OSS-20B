import React from 'react';
import { Search, Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface TopBarProps {
  searchPlaceholder?: string;
  onSearch?: (q: string) => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  searchPlaceholder = 'Search people, projects, technologies...',
  onSearch,
}) => {
  const user = JSON.parse(localStorage.getItem('ks_user') || '{"name":"User","email":""}');
  const navigate = useNavigate();

  return (
    <div className="h-14 bg-white border-b border-gray-100 flex items-center px-6 gap-4 sticky top-0 z-20">
      {/* Search */}
      <div className="flex-1 max-w-xl relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder={searchPlaceholder}
          className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm
                     focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-transparent"
          onChange={(e) => onSearch?.(e.target.value)}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 ml-auto">
        <button className="relative p-2 rounded-xl hover:bg-gray-100 transition-colors">
          <Bell size={18} className="text-gray-500" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-600" />
        </button>
        <button
          onClick={() => navigate('/dashboard')}
          className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-sm font-bold hover:bg-brand-700 transition-colors"
        >
          {user.name?.charAt(0)?.toUpperCase() || 'U'}
        </button>
      </div>
    </div>
  );
};
