import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { statsApi } from '../api';
import type { StatsOverview } from '../types';
import { Sparkles, ArrowRight, Play, Users, Briefcase, Cpu, Building2, UserCheck, FileText } from 'lucide-react';

// Animated floating node in hero
const FloatingNode: React.FC<{
  label: string;
  icon: React.ReactNode;
  color: string;
  style: React.CSSProperties;
  animClass: string;
}> = ({ label, icon, color, style, animClass }) => (
  <div
    className={`absolute flex flex-col items-center gap-1.5 ${animClass}`}
    style={style}
  >
    <div
      className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg backdrop-blur-sm"
      style={{ background: `${color}25`, border: `1.5px solid ${color}50` }}
    >
      <span style={{ color }}>{icon}</span>
    </div>
    <span className="text-white/70 text-xs font-medium bg-white/10 px-2 py-0.5 rounded-full backdrop-blur-sm">
      {label}
    </span>
  </div>
);

// Stat item in bottom bar
const StatItem: React.FC<{ label: string; value: number; icon: React.ReactNode }> = ({ label, value, icon }) => (
  <div className="flex flex-col items-center gap-1 flex-1 min-w-0">
    <div className="flex items-center gap-2">
      <span className="text-brand-300">{icon}</span>
      <span className="text-2xl font-bold text-white">{value.toLocaleString()}+</span>
    </div>
    <span className="text-white/50 text-xs font-medium">{label}</span>
  </div>
);

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<StatsOverview | null>(null);

  useEffect(() => {
    statsApi.overview().then(setStats).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #0F0E2A 0%, #1a0533 50%, #2d1b69 100%)' }}>
      {/* Top nav */}
      <nav className="flex items-center justify-between px-8 py-4 relative z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <span className="text-white font-bold text-lg">KnowSphere</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-white/60 text-sm font-medium">
          <button className="hover:text-white transition-colors">Product</button>
          <button className="hover:text-white transition-colors">Use Cases</button>
          <button className="hover:text-white transition-colors">Features</button>
          <button className="hover:text-white transition-colors">About</button>
        </div>
        <button
          id="get-started-nav"
          onClick={() => navigate('/login')}
          className="btn-primary text-sm px-5 py-2"
        >
          Get Started
        </button>
      </nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col md:flex-row items-center px-8 md:px-16 py-12 gap-8 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #7C3AED 0%, transparent 70%)' }} />

        {/* Left — headline */}
        <div className="flex-1 z-10 max-w-xl">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-4 py-1.5 mb-6">
            <Sparkles size={14} className="text-brand-400" />
            <span className="text-white/80 text-xs font-medium">GraphRAG-Powered Knowledge Explorer</span>
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
            Turn Enterprise<br />Knowledge Into{' '}
            <span className="gradient-text">Real Insights</span>
          </h1>
          <p className="text-white/60 text-lg mb-8 leading-relaxed">
            Explore the connections between people, projects, technologies, departments and more
            with the power of GraphRAG.
          </p>
          <div className="flex flex-wrap gap-4">
            <button
              id="hero-get-started"
              onClick={() => navigate('/login')}
              className="btn-primary flex items-center gap-2 text-base px-7 py-3"
            >
              Get Started <ArrowRight size={16} />
            </button>
            <button
              id="hero-watch-demo"
              onClick={() => navigate('/ask')}
              className="btn-secondary flex items-center gap-2 text-base px-7 py-3 border-white/30 text-white bg-white/10 hover:bg-white/20"
            >
              <Play size={16} /> Watch Demo
            </button>
          </div>
        </div>

        {/* Right — animated graph illustration */}
        <div className="flex-1 relative h-80 md:h-[420px] z-10 max-w-lg w-full">
          {/* Center hub */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
            <div className="w-16 h-16 rounded-2xl bg-brand-600 flex items-center justify-center shadow-glow animate-pulse-glow">
              <Sparkles size={24} className="text-white" />
            </div>
          </div>

          {/* Connecting lines (SVG) */}
          <svg className="absolute inset-0 w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
            <line x1="50%" y1="50%" x2="20%" y2="20%" stroke="#7C3AED" strokeWidth="1.5" strokeDasharray="4,4" />
            <line x1="50%" y1="50%" x2="80%" y2="20%" stroke="#4F46E5" strokeWidth="1.5" strokeDasharray="4,4" />
            <line x1="50%" y1="50%" x2="15%" y2="65%" stroke="#7C3AED" strokeWidth="1.5" strokeDasharray="4,4" />
            <line x1="50%" y1="50%" x2="85%" y2="65%" stroke="#4F46E5" strokeWidth="1.5" strokeDasharray="4,4" />
            <line x1="50%" y1="50%" x2="50%" y2="15%" stroke="#7C3AED" strokeWidth="1.5" strokeDasharray="4,4" />
            <line x1="50%" y1="50%" x2="50%" y2="85%" stroke="#4F46E5" strokeWidth="1.5" strokeDasharray="4,4" />
          </svg>

          {/* Floating nodes */}
          <FloatingNode label="People" icon={<Users size={22} />} color="#3B82F6"
            style={{ top: '5%', left: '15%' }} animClass="animate-float" />
          <FloatingNode label="Projects" icon={<Briefcase size={22} />} color="#8B5CF6"
            style={{ top: '5%', right: '15%' }} animClass="animate-float-delayed" />
          <FloatingNode label="Technologies" icon={<Cpu size={22} />} color="#F97316"
            style={{ top: '40%', left: '2%' }} animClass="animate-float-slow" />
          <FloatingNode label="Departments" icon={<Building2 size={22} />} color="#22C55E"
            style={{ top: '40%', right: '2%' }} animClass="animate-float" />
          <FloatingNode label="Documents" icon={<FileText size={22} />} color="#6366F1"
            style={{ bottom: '5%', left: '20%' }} animClass="animate-float-delayed" />
          <FloatingNode label="Customers" icon={<UserCheck size={22} />} color="#EC4899"
            style={{ bottom: '5%', right: '20%' }} animClass="animate-float-slow" />
        </div>
      </div>

      {/* Stats bar — LIVE from API */}
      <div className="border-t border-white/10 bg-black/20 backdrop-blur-sm py-6 px-8">
        {stats ? (
          <div className="max-w-5xl mx-auto flex flex-wrap justify-around gap-6">
            <StatItem label="Employees" value={stats.employees} icon={<Users size={16} />} />
            <StatItem label="Projects" value={stats.projects} icon={<Briefcase size={16} />} />
            <StatItem label="Technologies" value={stats.technologies} icon={<Cpu size={16} />} />
            <StatItem label="Departments" value={stats.departments} icon={<Building2 size={16} />} />
            <StatItem label="Customers" value={stats.customers} icon={<UserCheck size={16} />} />
            <StatItem label="Documents" value={stats.documents} icon={<FileText size={16} />} />
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="spinner" />
          </div>
        )}
      </div>
    </div>
  );
};
