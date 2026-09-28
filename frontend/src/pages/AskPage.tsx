import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { MobileTabBar } from '../components/MobileTabBar';
import { askApi, chatApi } from '../api';
import type { AskResponse, ChatMessage } from '../types';
import { Send, ThumbsUp, ThumbsDown, Share2, Loader2, Sparkles, User } from 'lucide-react';
import toast from 'react-hot-toast';

// Entity type colors for source pills
const SOURCE_COLORS: Record<string, string> = {
  docx: 'bg-blue-100 text-blue-700',
  xlsx: 'bg-green-100 text-green-700',
  pdf: 'bg-red-100 text-red-700',
  default: 'bg-gray-100 text-gray-700',
};

const StructuredAnswer: React.FC<{ answer: AskResponse; onViewGraph: () => void }> = ({ answer, onViewGraph }) => (
  <div className="space-y-4">
    {/* Summary */}
    <p className="text-gray-700 text-sm leading-relaxed">{answer.answer}</p>

    {/* Findings */}
    {answer.findings?.length > 0 && (
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Findings</h4>
        <ol className="space-y-1.5">
          {answer.findings.map((f, i) => (
            <li key={i} className="flex gap-2 text-sm text-gray-700">
              <span className="text-brand-600 font-bold flex-shrink-0">{i + 1}.</span>
              <span dangerouslySetInnerHTML={{ __html: f.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
            </li>
          ))}
        </ol>
      </div>
    )}

    {/* Graph path */}
    {answer.graph_path_explanation && (
      <div className="bg-brand-50 border border-brand-100 rounded-xl p-3">
        <p className="text-xs font-semibold text-brand-700 mb-1">Graph Path Used</p>
        <p className="text-sm text-brand-800 font-mono">{answer.graph_path_explanation}</p>
      </div>
    )}

    {/* Sources */}
    {answer.sources?.length > 0 && (
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Sources</h4>
        <div className="flex flex-wrap gap-2">
          {answer.sources.map((s, i) => {
            const ext = s.name.split('.').pop() || 'default';
            return (
              <span key={i} className={`text-xs px-2.5 py-1 rounded-full font-medium ${SOURCE_COLORS[ext] || SOURCE_COLORS.default}`}>
                {s.name}
              </span>
            );
          })}
        </div>
      </div>
    )}

    {/* Actions */}
    <div className="flex items-center gap-3 pt-1 border-t border-gray-100">
      <button className="p-1.5 rounded-lg hover:bg-green-50 text-gray-400 hover:text-green-600 transition-colors">
        <ThumbsUp size={16} />
      </button>
      <button className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
        <ThumbsDown size={16} />
      </button>
      <div className="flex-1" />
      {(answer.subgraph_node_ids?.length > 0 || answer.subgraph) && (
        <button
          id="view-graph-btn"
          onClick={onViewGraph}
          className="flex items-center gap-1.5 text-xs font-semibold text-brand-600 border border-brand-200 px-3 py-1.5 rounded-full hover:bg-brand-50 transition-colors"
        >
          <Share2 size={13} /> View Graph
        </button>
      )}
    </div>
  </div>
);

export const AskPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string; data?: AskResponse }>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('Searching knowledge graph...');
  const [sessionId, setSessionId] = useState<string | undefined>(searchParams.get('session') || undefined);
  const [suggestions, setSuggestions] = useState<string[]>([
    'Which projects depend on technologies used by Team A?',
    'Show all employees working on Project Phoenix',
    'What technologies are used by the Marketing department?',
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load existing session if navigated from history
  useEffect(() => {
    const sid = searchParams.get('session');
    if (sid) {
      chatApi.session(sid).then((thread) => {
        const msgs = thread.messages.map((m: ChatMessage) => ({
          role: m.role,
          content: m.content,
          data: m.structured_answer ?? undefined,
        }));
        setMessages(msgs);
        setSessionId(sid);
      }).catch(() => {});
    }
  }, []);

  const handleSend = async (question?: string) => {
    const q = question || input.trim();
    if (!q) return;
    setInput('');
    setLoading(true);
    setLoadingStep('Searching knowledge graph & documents...');
    setSuggestions([]);

    const stepTimer = setTimeout(() => {
      setLoadingStep('Synthesizing structured answer...');
    }, 300);

    const userMsg = { role: 'user' as const, content: q };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res: AskResponse = await askApi.ask(q, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.answer, data: res }]);
      setSuggestions(res.follow_up_suggestions || []);
    } catch (err: any) {
      toast.error('Failed to get answer. Please try again.');
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }]);
    } finally {
      clearTimeout(stepTimer);
      setLoading(false);
    }
  };

  const handleViewGraph = (data: AskResponse) => {
    if (data.subgraph_node_ids?.length > 0) {
      navigate(`/graph?highlight=${data.subgraph_node_ids.join(',')}`);
    } else {
      navigate('/graph');
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="page-with-sidebar flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-100 px-6 py-4">
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles size={20} className="text-brand-600" /> Ask Anything
          </h1>
          <p className="text-gray-500 text-sm mt-0.5">Get accurate, evidence-backed answers using GraphRAG.</p>
        </div>

        {/* Chat thread */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center">
              <div className="w-16 h-16 rounded-2xl bg-brand-100 flex items-center justify-center mb-4">
                <Sparkles size={28} className="text-brand-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Ask about your organization</h2>
              <p className="text-gray-400 text-sm max-w-sm">
                I can answer relationship-heavy questions using knowledge graph traversal and semantic search.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} gap-3`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center flex-shrink-0 mt-1">
                  <Sparkles size={14} className="text-brand-600" />
                </div>
              )}
              <div className={`max-w-2xl ${msg.role === 'user' ? 'chat-user' : 'chat-assistant'}`}>
                {msg.role === 'user' ? (
                  <p>{msg.content}</p>
                ) : msg.data ? (
                  <StructuredAnswer answer={msg.data} onViewGraph={() => handleViewGraph(msg.data!)} />
                ) : (
                  <p className="text-sm">{msg.content}</p>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center flex-shrink-0 mt-1">
                  <User size={14} className="text-white" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex justify-start gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center animate-pulse flex-shrink-0 mt-1">
                <Sparkles size={14} className="text-brand-600" />
              </div>
              <div className="chat-assistant flex items-center gap-2.5 text-gray-600 text-sm py-2 px-3.5 bg-brand-50/50 border border-brand-100 rounded-2xl shadow-sm">
                <Loader2 size={15} className="animate-spin text-brand-600" />
                <span className="font-medium text-xs text-brand-700">{loadingStep}</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Follow-up suggestions */}
        {suggestions.length > 0 && (
          <div className="px-4 md:px-8 pb-3 flex flex-wrap gap-2">
            {suggestions.map((s, i) => (
              <button
                key={i}
                id={`suggestion-${i}`}
                onClick={() => handleSend(s)}
                className="text-xs bg-white border border-brand-200 text-brand-700 px-3 py-1.5 rounded-full
                           hover:bg-brand-50 transition-colors font-medium max-w-xs truncate"
                title={s}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input bar */}
        <div className="bg-white border-t border-gray-100 px-4 md:px-8 py-4">
          <div className="flex gap-3 items-end max-w-4xl mx-auto">
            <textarea
              id="ask-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask a follow up question..."
              rows={1}
              className="flex-1 input-field resize-none min-h-[42px] max-h-32 py-2.5"
              style={{ height: 'auto' }}
            />
            <button
              id="ask-send-btn"
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="btn-primary p-2.5 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>
      <MobileTabBar />
    </div>
  );
};
