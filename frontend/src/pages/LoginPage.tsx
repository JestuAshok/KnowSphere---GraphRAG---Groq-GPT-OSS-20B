import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api';
import { Sparkles, Eye, EyeOff, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('demo@knowsphere.ai');
  const [password, setPassword] = useState('demo1234');
  const [name, setName] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = isRegister
        ? await authApi.register(email, name, password)
        : await authApi.login(email, password);
      localStorage.setItem('ks_token', res.access_token);
      localStorage.setItem('ks_user', JSON.stringify({ id: res.user_id, name: res.name, email: res.email }));
      toast.success(`Welcome, ${res.name}!`);
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((d: any) => d?.msg || JSON.stringify(d)).join(', ')
        : (typeof detail === 'string' ? detail : 'Authentication failed');
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center"
      style={{ background: 'linear-gradient(135deg, #0F0E2A 0%, #1a0533 50%, #2d1b69 100%)' }}>
      <div className="w-full max-w-md mx-4">
        <button onClick={() => navigate('/')} className="text-white/60 flex items-center gap-2 text-sm mb-6 hover:text-white transition-colors">
          <ArrowLeft size={16} /> Back to home
        </button>
        <div className="bg-white rounded-3xl shadow-2xl p-8">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
              <Sparkles size={18} className="text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">KnowSphere</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">
            {isRegister ? 'Create account' : 'Welcome back'}
          </h2>
          <p className="text-gray-500 text-sm mb-6">
            {isRegister ? 'Start exploring your knowledge graph' : 'Sign in to continue'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1.5">Full name</label>
                <input id="login-name" className="input-field" placeholder="Alice Smith"
                  value={name} onChange={(e) => setName(e.target.value)} required={isRegister} />
              </div>
            )}
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1.5">Email</label>
              <input id="login-email" type="email" className="input-field" placeholder="you@company.com"
                value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1.5">Password</label>
              <div className="relative">
                <input id="login-password" type={showPw ? 'text' : 'password'} className="input-field pr-10"
                  placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <button id="login-submit" type="submit" disabled={loading}
              className="btn-primary w-full text-base py-3 flex items-center justify-center gap-2">
              {loading ? <div className="spinner" /> : (isRegister ? 'Create Account' : 'Sign In')}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-5">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button onClick={() => setIsRegister(!isRegister)}
              className="text-brand-600 font-semibold hover:underline">
              {isRegister ? 'Sign in' : 'Sign up'}
            </button>
          </p>

          {!isRegister && (
            <div className="mt-4 p-3 bg-brand-50 rounded-xl border border-brand-100">
              <p className="text-xs text-brand-700 font-medium">Demo credentials pre-filled ↑</p>
              <p className="text-xs text-brand-600 mt-0.5">demo@knowsphere.ai / demo1234</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
