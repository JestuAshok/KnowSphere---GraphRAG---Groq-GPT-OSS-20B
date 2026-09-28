import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: number | string;
  change?: number;
  icon: React.ReactNode;
  color?: string;
  description?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title, value, change, icon, color = '#7C3AED', description
}) => {
  const isPositive = (change ?? 0) >= 0;

  return (
    <div className="stat-card animate-fade-up">
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-11 h-11 rounded-xl flex items-center justify-center"
          style={{ background: `${color}15` }}
        >
          <span style={{ color }}>{icon}</span>
        </div>
        {change !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full
            ${isPositive ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'}`}>
            {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div className="text-sm font-medium text-gray-500">{title}</div>
      {description && <div className="text-xs text-gray-400 mt-1">{description}</div>}
    </div>
  );
};
