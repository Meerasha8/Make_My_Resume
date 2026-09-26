import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../api';
import { Mail, Lock, User, Sparkles, FileText, MessageSquare } from 'lucide-react';
import Logo from '../components/Logo';

const FEATURES = [
  { icon: FileText, title: 'Tailored resumes', text: 'Paste a job description and get a DOCX resume built from your best-matching experience.' },
  { icon: MessageSquare, title: 'AI portfolio assistant', text: 'Ask questions about your own projects, skills and experience.' },
  { icon: Sparkles, title: 'One place for your profile', text: 'Keep projects, skills, education and certificates organised.' },
];

const Field = ({ icon: Icon, label, ...inputProps }) => (
  <div>
    <label className="label">{label}</label>
    <div className="relative">
      <Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-400" />
      <input required className="input pl-10" {...inputProps} />
    </div>
  </div>
);

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSlow, setIsSlow] = useState(false);
  const { login } = useAuth();

  // The free Render backend sleeps when idle; the first request can take ~50s while it wakes up.
  useEffect(() => {
    if (!isLoading) return undefined;
    const timer = setTimeout(() => setIsSlow(true), 5000);
    return () => { clearTimeout(timer); setIsSlow(false); };
  }, [isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const body = isLogin ? { email, password } : { username, email, password };

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Authentication failed');
      }

      if (isLogin) {
        login(data.access_token, data.user);
      } else {
        setIsLogin(true); // Switch to login after successful registration
        setError('Registration successful. Please log in.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const isSuccess = isLogin && error.includes('successful');

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <aside className="relative hidden overflow-hidden bg-gradient-to-br from-brand-600 via-brand-700 to-brand-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand-400/30 blur-3xl" />
        <div className="absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-brand-300/20 blur-3xl" />
        <Logo inverted className="relative" />
        <div className="relative max-w-md">
          <h2 className="text-4xl font-extrabold leading-tight">Build a resume that fits every job.</h2>
          <p className="mt-4 text-brand-100">
            Store your experience once, then let AI pick and polish what matters for each role.
          </p>
          <ul className="mt-10 space-y-5">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <li key={title} className="flex gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/10 ring-1 ring-white/20">
                  <Icon className="h-5 w-5" />
                </span>
                <div>
                  <p className="font-semibold">{title}</p>
                  <p className="text-sm text-brand-100">{text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-sm text-brand-200">© {new Date().getFullYear()} Make My Resume</p>
      </aside>

      {/* Form panel */}
      <section className="flex items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 py-12 sm:px-6">
        <div className="w-full max-w-md">
          <Logo className="mb-8 justify-center lg:hidden" />

          <div className="card p-6 sm:p-8">
            <h1 className="text-2xl font-bold text-brand-950">{isLogin ? 'Welcome back' : 'Create your account'}</h1>
            <p className="mt-1 text-sm text-slate-500">
              {isLogin ? 'Sign in to continue building your resume.' : 'It only takes a minute to get started.'}
            </p>

            <div className="mt-6 grid grid-cols-2 rounded-lg bg-brand-50 p-1 text-sm font-semibold">
              {[['Sign in', true], ['Sign up', false]].map(([label, value]) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => { setIsLogin(value); setError(''); }}
                  className={`rounded-md py-2 transition ${isLogin === value ? 'bg-white text-brand-700 shadow-sm' : 'text-slate-500 hover:text-brand-700'}`}
                >
                  {label}
                </button>
              ))}
            </div>

            {error && <div className={`mt-6 ${isSuccess ? 'alert-success' : 'alert-error'}`}>{error}</div>}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {!isLogin && (
                <Field icon={User} label="Username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="johndoe" />
              )}
              <Field icon={Mail} label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
              <Field icon={Lock} label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />

              <button type="submit" disabled={isLoading} className="btn-primary w-full py-3">
                {isLoading ? 'Please wait...' : isLogin ? 'Sign in' : 'Create account'}
              </button>
              {isSlow && (
                <p className="text-center text-xs text-slate-500">
                  Waking up the server. The first request after a quiet period can take up to a minute.
                </p>
              )}
            </form>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Login;
