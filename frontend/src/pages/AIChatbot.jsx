import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../api';
import { MessageSquare, Send, PlusCircle, Bot, User, History, X } from 'lucide-react';

const SUGGESTIONS = [
  'What projects have I built?',
  'Summarise my technical skills',
  'Which internship fits a backend role best?',
];

const AIChatbot = () => {
  const { token } = useAuth();
  const [history, setHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const fetchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/ai/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        setHistory(data.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch chat history', err);
    }
  };

  useEffect(() => {
    if (token) fetchHistory();
  }, [token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendQuestion = async (question) => {
    if (!question.trim()) return;

    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE_URL}/ai/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ question })
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || data.message || `AI request failed (${response.status})`);
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }]);
      fetchHistory(); // Refresh sidebar history
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `Unable to answer right now: ${err.message}` }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    sendQuestion(input);
  };

  const handleNewChat = () => {
    setMessages([]);
    setIsHistoryOpen(false);
  };

  const loadPastChat = (item) => {
    setMessages([
      { role: 'user', content: item.question },
      { role: 'assistant', content: item.answer }
    ]);
    setIsHistoryOpen(false);
  };

  return (
    <div className="card relative flex h-[calc(100dvh-7rem)] min-h-[28rem] overflow-hidden lg:h-[calc(100dvh-10rem)]">
      {/* History: fixed sidebar on desktop, slide-over drawer on mobile */}
      {isHistoryOpen && (
        <button className="absolute inset-0 z-10 bg-brand-950/30 md:hidden" onClick={() => setIsHistoryOpen(false)} aria-label="Close history" />
      )}
      <aside
        className={`absolute inset-y-0 left-0 z-20 flex w-72 max-w-[85%] flex-col border-r border-brand-100 bg-brand-50 transition-transform md:static md:max-w-none md:translate-x-0 ${
          isHistoryOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-2 border-b border-brand-100 p-4">
          <button onClick={handleNewChat} className="btn-primary flex-1">
            <PlusCircle className="h-4 w-4" />
            New chat
          </button>
          <button onClick={() => setIsHistoryOpen(false)} className="btn-icon md:hidden" aria-label="Close history">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3">
          <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-brand-500">Recent questions</h3>
          {history.length === 0 ? (
            <p className="px-2 text-sm text-slate-400">No history yet.</p>
          ) : (
            history.map((item) => (
              <button
                key={item.id}
                onClick={() => loadPastChat(item)}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:bg-white hover:text-brand-700"
              >
                <MessageSquare className="h-3.5 w-3.5 shrink-0 text-brand-400" />
                <span className="truncate">{item.question}</span>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-brand-100 px-4 py-3">
          <button onClick={() => setIsHistoryOpen(true)} className="btn-icon md:hidden" aria-label="Show history">
            <History className="h-5 w-5" />
          </button>
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-white">
            <Bot className="h-5 w-5" />
          </span>
          <div>
            <p className="font-semibold text-brand-950">Resume assistant</p>
            <p className="text-xs text-slate-500">Answers using your portfolio data</p>
          </div>
        </div>

        {messages.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto p-6 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50">
              <Bot className="h-8 w-8 text-brand-600" />
            </div>
            <h2 className="mb-2 text-xl font-bold text-brand-950 sm:text-2xl">How can I help you today?</h2>
            <p className="max-w-md text-sm text-slate-500">
              Ask about your portfolio, experience, skills or projects. I only use the data you've added.
            </p>
            <div className="mt-6 flex max-w-lg flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendQuestion(suggestion)}
                  className="rounded-full border border-brand-200 bg-white px-3.5 py-1.5 text-sm text-brand-700 transition hover:border-brand-400 hover:bg-brand-50"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 space-y-5 overflow-y-auto bg-gradient-to-b from-white to-brand-50/40 p-4 sm:p-6">
            {messages.map((msg, index) => (
              <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex max-w-[90%] gap-3 sm:max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                    msg.role === 'user' ? 'bg-brand-600 text-white' : 'bg-brand-100 text-brand-700'
                  }`}>
                    {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>
                  <div className={`rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'rounded-tr-sm bg-brand-600 text-white'
                      : 'rounded-tl-sm border border-brand-100 bg-white text-slate-800 shadow-sm'
                  }`}>
                    <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{msg.content}</p>
                  </div>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm border border-brand-100 bg-white px-4 py-3">
                  {[0, 150, 300].map((delay) => (
                    <div key={delay} className="h-2 w-2 animate-bounce rounded-full bg-brand-400" style={{ animationDelay: `${delay}ms` }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input area */}
        <div className="border-t border-brand-100 bg-white p-3 sm:p-4">
          <form onSubmit={handleSend} className="relative mx-auto flex max-w-3xl items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your portfolio..."
              className="input rounded-full bg-brand-50/50 py-3 pl-5 pr-14"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-1.5 flex h-10 w-10 items-center justify-center rounded-full bg-brand-600 text-white transition hover:bg-brand-700 disabled:opacity-50"
              aria-label="Send"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AIChatbot;
