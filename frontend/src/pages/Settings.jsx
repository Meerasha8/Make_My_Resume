import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../api';
import { User, Mail, Phone, MapPin, Link as LinkIcon, Briefcase, Save, LogOut, Settings as SettingsIcon } from 'lucide-react';
import PageHeader from '../components/PageHeader';

const PROFILE_FIELDS = [
  { name: 'name', label: 'Full name', icon: User, type: 'text', placeholder: 'John Doe' },
  { name: 'mobile_number', label: 'Mobile number', icon: Phone, type: 'text', placeholder: '+1 234 567 8900' },
  { name: 'email_id', label: 'Contact email', icon: Mail, type: 'email', placeholder: 'contact@example.com' },
  { name: 'location', label: 'Location', icon: MapPin, type: 'text', placeholder: 'New York, USA' },
  { name: 'linkedin_url', label: 'LinkedIn URL', icon: LinkIcon, type: 'url', placeholder: 'https://linkedin.com/in/johndoe' },
  { name: 'github_url', label: 'GitHub URL', icon: LinkIcon, type: 'url', placeholder: 'https://github.com/johndoe' },
  { name: 'portfolio_link', label: 'Portfolio link', icon: LinkIcon, type: 'url', placeholder: 'https://johndoe.com', fullWidth: true },
];

const Settings = () => {
  const { token, logout, user } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    mobile_number: '',
    email_id: '',
    github_url: '',
    linkedin_url: '',
    portfolio_link: '',
    location: '',
    profession_summary: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/user-details/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          if (data && Object.keys(data).length > 0) {
            setFormData(prev => ({ ...prev, ...data }));
          }
        }
      } catch (err) {
        console.error('Failed to fetch profile', err);
      }
    };
    if (token) fetchProfile();
  }, [token]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');
    setIsError(false);

    try {
      const response = await fetch(`${API_BASE_URL}/user-details/upsert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to update profile');
      }

      setMessage('Profile updated successfully!');
    } catch (err) {
      setIsError(true);
      setMessage(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const displayName = formData.name || user?.username || 'Your profile';

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader icon={SettingsIcon} title="Settings" subtitle="These details appear at the top of every resume you generate." />

      <div className="space-y-6">
        {/* Account header */}
        <section className="card overflow-hidden">
          <div className="h-20 bg-gradient-to-r from-brand-500 via-brand-600 to-brand-800 sm:h-24" />
          <div className="flex flex-col gap-4 px-5 pb-5 sm:flex-row sm:items-end sm:justify-between sm:px-6">
            <div className="flex items-end gap-4">
              <div className="-mt-10 flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl border-4 border-white bg-brand-100 text-2xl font-bold text-brand-700 shadow-md">
                {displayName.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 pb-1">
                <h2 className="truncate text-lg font-bold text-brand-950">{displayName}</h2>
                <p className="truncate text-sm text-slate-500">{user?.email || formData.email_id || 'Signed in'}</p>
              </div>
            </div>
            <button onClick={logout} className="btn-danger self-start sm:self-auto">
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </section>

        {/* Profile form */}
        <section className="card p-5 sm:p-6">
          <h3 className="mb-5 border-b border-brand-100 pb-4 text-lg font-semibold text-brand-950">Personal information</h3>

          {message && <div className={`mb-5 ${isError ? 'alert-error' : 'alert-success'}`}>{message}</div>}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              {PROFILE_FIELDS.map(({ name, label, icon: Icon, type, placeholder, fullWidth }) => (
                <div key={name} className={fullWidth ? 'md:col-span-2' : ''}>
                  <label htmlFor={name} className="label">{label}</label>
                  <div className="relative">
                    <Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-400" />
                    <input
                      id={name}
                      type={type}
                      name={name}
                      value={formData[name] || ''}
                      onChange={handleChange}
                      className="input pl-10"
                      placeholder={placeholder}
                    />
                  </div>
                </div>
              ))}

              <div className="md:col-span-2">
                <label htmlFor="profession_summary" className="label">Professional summary</label>
                <div className="relative">
                  <Briefcase className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-brand-400" />
                  <textarea
                    id="profession_summary"
                    name="profession_summary"
                    value={formData.profession_summary || ''}
                    onChange={handleChange}
                    rows={4}
                    className="input resize-y pl-10"
                    placeholder="Experienced software engineer with a focus on..."
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end border-t border-brand-100 pt-5">
              <button type="submit" disabled={isLoading} className="btn-primary w-full sm:w-auto sm:px-6">
                <Save className="h-4 w-4" />
                {isLoading ? 'Saving...' : 'Save changes'}
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
};

export default Settings;
