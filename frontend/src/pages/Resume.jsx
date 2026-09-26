import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../api';
import { FileText, Download, Clock, Sparkles, Trash2 } from 'lucide-react';
import PageHeader from '../components/PageHeader';

const STATUS_STYLES = {
  completed: 'bg-brand-100 text-brand-700',
  failed: 'bg-red-100 text-red-700',
};

const Resume = () => {
  const { token } = useAuth();
  const [jobDescription, setJobDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  const fetchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/resume/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        setHistory(data.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch resume history', err);
    }
  };

  useEffect(() => {
    if (token) fetchHistory();
  }, [token]);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!jobDescription.trim()) return;

    setIsGenerating(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/resume/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ job_description: jobDescription })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Generation failed');
      }

      setJobDescription('');
      fetchHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDelete = async (historyId) => {
    if (!window.confirm('Delete this generated resume from your history?')) return;

    setDeletingId(historyId);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/resume/history/${historyId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Could not delete resume');
      }
      setHistory((previousHistory) => previousHistory.filter((item) => item.id !== historyId));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <PageHeader icon={FileText} title="Resume generator" subtitle="Create a DOCX resume tailored to a specific job." />

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Generation form */}
        <section className="card p-5 sm:p-6 lg:col-span-3">
          <h2 className="text-lg font-semibold text-brand-950">Job description</h2>
          <p className="mb-5 mt-1 text-sm text-slate-500">
            Paste the job posting and AI will select and rewrite your most relevant experience for it.
          </p>

          {error && <div className="alert-error mb-4">{error}</div>}

          <form onSubmit={handleGenerate}>
            <textarea
              rows={12}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
              className="input resize-y"
              required
            />
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-slate-400">{jobDescription.trim().split(/\s+/).filter(Boolean).length} words</p>
              <button type="submit" disabled={isGenerating} className="btn-primary sm:px-6">
                <Sparkles className="h-4 w-4" />
                {isGenerating ? 'Generating...' : 'Generate resume'}
              </button>
            </div>
          </form>
        </section>

        {/* History */}
        <section className="card flex flex-col p-5 sm:p-6 lg:col-span-2">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-brand-950">
            <Clock className="h-5 w-5 text-brand-500" />
            Generation history
          </h2>

          {history.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center py-10 text-center">
              <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-400">
                <FileText className="h-6 w-6" />
              </span>
              <p className="text-sm text-slate-500">No resumes generated yet.</p>
            </div>
          ) : (
            <ul className="space-y-3 lg:max-h-[32rem] lg:overflow-y-auto lg:pr-1">
              {history.map((item) => (
                <li key={item.id} className="rounded-xl border border-brand-100 p-4 transition hover:border-brand-300 hover:bg-brand-50/40">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${STATUS_STYLES[item.status] || 'bg-amber-100 text-amber-800'}`}>
                      {item.status}
                    </span>
                    <span className="text-xs text-slate-500">{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="mb-3 line-clamp-2 text-sm text-slate-700">{item.job_description}</p>
                  <div className="flex flex-wrap justify-end gap-2">
                    {item.status === 'completed' && item.download_url && (
                      <a
                        href={`${API_BASE_URL}${item.download_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-secondary px-3 py-2"
                      >
                        <Download className="h-4 w-4" />
                        Download DOCX
                      </a>
                    )}
                    <button
                      type="button"
                      onClick={() => handleDelete(item.id)}
                      disabled={deletingId === item.id}
                      className="btn-danger"
                    >
                      <Trash2 className="h-4 w-4" />
                      {deletingId === item.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
};

export default Resume;
