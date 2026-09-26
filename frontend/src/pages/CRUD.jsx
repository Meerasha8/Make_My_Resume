import React, { useEffect, useState } from 'react';
import { Award, Briefcase, Code, Edit3, Eye, GraduationCap, LayoutDashboard, PenTool, Plus, Star, Trash2, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../api';
import PageHeader from '../components/PageHeader';

const TABS = [
  { id: 'projects', label: 'Projects', singular: 'project', icon: Briefcase },
  { id: 'skills', label: 'Skills', singular: 'skill', icon: PenTool },
  { id: 'education', label: 'Education', singular: 'education', icon: GraduationCap },
  { id: 'internships', label: 'Internships', singular: 'internship', icon: Code },
  { id: 'certificates', label: 'Certificates', singular: 'certificate', icon: Award },
  { id: 'achievements', label: 'Achievements', singular: 'achievement', icon: Star },
];

const SECTION_CONFIG = {
  projects: {
    endpoint: '/projects/',
    addEndpoint: '/projects/add-project',
    editEndpoint: (id) => `/projects/edit-project/${id}`,
    deleteEndpoint: (id) => `/projects/delete-project/${id}`,
    responseKey: 'projects',
    fields: [['name', 'Project name'], ['description', 'Description', 'textarea', 'What problem does it solve, what did you build (features, tech), and what was the result (users, speed, accuracy, deployment)?'], ['tech_stack', 'Technology stack'], ['github_url', 'GitHub URL', 'url'], ['live_link', 'Live link', 'url']],
  },
  skills: {
    endpoint: '/skills/',
    addEndpoint: '/skills/add-skill',
    editEndpoint: (id) => `/skills/edit-skill/${id}`,
    deleteEndpoint: (id) => `/skills/delete-skill/${id}`,
    fields: [['name', 'Skill name'], ['description', 'Description', 'textarea']],
  },
  education: {
    endpoint: '/education/',
    addEndpoint: '/education/add-education',
    editEndpoint: (id) => `/education/edit-education/${id}`,
    deleteEndpoint: (id) => `/education/delete-education/${id}`,
    responseKey: 'Educations',
    fields: [['course_name', 'Course name'], ['cgpa', 'CGPA', 'number'], ['start_year', 'Start year', 'number'], ['end_year', 'End year', 'number'], ['college_name', 'College name'], ['location', 'Location']],
  },
  internships: {
    endpoint: '/internship/',
    addEndpoint: '/internship/add-internship',
    editEndpoint: (id) => `/internship/edit-internship/${id}`,
    deleteEndpoint: (id) => `/internship/delete-internship/${id}`,
    responseKey: 'internship',
    fields: [['company_name', 'Company name'], ['role', 'Role'], ['description', 'Description', 'textarea', 'What problem did you work on, what did you build, and what was the result?'], ['duration', 'Duration']],
  },
  certificates: {
    endpoint: '/certificates/',
    addEndpoint: '/certificates/add-certificate',
    editEndpoint: (id) => `/certificates/edit-certificate/${id}`,
    deleteEndpoint: (id) => `/certificates/delete-certificate/${id}`,
    responseKey: 'certificates',
    fields: [['certificate_name', 'Certificate name'], ['certificate_issuer', 'Issuer']],
  },
  achievements: {
    endpoint: '/achievement/',
    addEndpoint: '/achievement/add-achievement',
    editEndpoint: (id) => `/achievement/edit-achievement/${id}`,
    deleteEndpoint: (id) => `/achievement/delete-achievement/${id}`,
    responseKey: 'Achievements',
    fields: [['description', 'Achievement', 'textarea']],
  },
};

const emptyForm = (fields) => Object.fromEntries(fields.map(([name]) => [name, '']));

const CRUD = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('projects');
  const [items, setItems] = useState([]);
  const [formData, setFormData] = useState({});
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [viewingItem, setViewingItem] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const config = SECTION_CONFIG[activeTab];
  const activeSection = TABS.find((tab) => tab.id === activeTab);
  const ActiveIcon = activeSection.icon;

  const loadItems = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}${config.endpoint}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not load this section');
      setItems(config.responseKey ? data[config.responseKey] || [] : data || []);
    } catch (requestError) {
      setError(requestError.message);
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadItems();
  }, [activeTab, token]);

  const selectTab = (tabId) => {
    setActiveTab(tabId);
    setIsFormOpen(false);
    setEditingItem(null);
    setViewingItem(null);
    setMessage('');
    setError('');
  };

  const openForm = () => {
    setFormData(emptyForm(config.fields));
    setEditingItem(null);
    setViewingItem(null);
    setIsFormOpen(true);
    setMessage('');
    setError('');
  };

  const openEditForm = (item) => {
    setFormData(Object.fromEntries(config.fields.map(([name]) => [name, item[name] ?? ''])));
    setEditingItem(item);
    setViewingItem(null);
    setIsFormOpen(true);
    setMessage('');
    setError('');
  };

  const closeForm = () => {
    setIsFormOpen(false);
    setEditingItem(null);
  };

  const handleDelete = async (item) => {
    if (!window.confirm('Delete this item from your portfolio?')) return;
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}${config.deleteEndpoint(item.id)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || data.message || 'Could not delete this item');
      setItems((currentItems) => currentItems.filter((currentItem) => currentItem.id !== item.id));
      setMessage('Deleted successfully.');
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    setMessage('');

    const payload = { ...formData };
    config.fields.forEach(([name, , type]) => {
      if (type === 'number') payload[name] = Number(payload[name]);
    });

    try {
      const response = await fetch(`${API_BASE_URL}${editingItem ? config.editEndpoint(editingItem.id) : config.addEndpoint}`, {
        method: editingItem ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || data.message || 'Could not save this item');
      closeForm();
      setMessage(editingItem ? 'Updated successfully.' : 'Added successfully.');
      await loadItems();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <PageHeader
        icon={LayoutDashboard}
        title="Portfolio dashboard"
        subtitle="Everything you add here can be used to build your resumes."
        actions={
          <button onClick={openForm} className="btn-primary">
            <Plus className="h-4 w-4" /> Add {activeSection.singular}
          </button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[15rem_1fr]">
        {/* Section navigation: horizontal scroller on small screens, sidebar on large */}
        <nav className="card scrollbar-none flex gap-2 overflow-x-auto p-2 lg:sticky lg:top-24 lg:flex-col lg:self-start lg:p-3">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => selectTab(tab.id)}
                className={`flex shrink-0 items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/25' : 'text-slate-600 hover:bg-brand-50 hover:text-brand-700'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-white' : 'text-brand-400'}`} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        <section className="min-w-0 space-y-4">
          {error && <div className="alert-error">{error}</div>}
          {message && <div className="alert-success">{message}</div>}

          {isFormOpen && (
            <form onSubmit={handleSubmit} className="card p-5 sm:p-6">
              <div className="mb-5 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-brand-950">{editingItem ? 'Edit' : 'Add'} {activeSection.singular}</h2>
                <button type="button" onClick={closeForm} className="btn-icon" aria-label="Close form">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {config.fields.map(([name, label, type, placeholder]) => (
                  <label key={name} className={type === 'textarea' ? 'sm:col-span-2' : ''}>
                    <span className="label">{label}</span>
                    {type === 'textarea' ? (
                      <textarea required name={name} placeholder={placeholder} value={formData[name] || ''} onChange={(event) => setFormData({ ...formData, [name]: event.target.value })} rows={3} className="input resize-y" />
                    ) : (
                      <input required type={type || 'text'} step={type === 'number' ? 'any' : undefined} name={name} value={formData[name] || ''} onChange={(event) => setFormData({ ...formData, [name]: event.target.value })} className="input" />
                    )}
                  </label>
                ))}
              </div>
              <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                <button type="button" onClick={closeForm} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={isSaving} className="btn-primary">
                  {isSaving ? 'Saving...' : editingItem ? 'Update' : 'Save'}
                </button>
              </div>
            </form>
          )}

          {viewingItem && (
            <div className="card border-brand-200 bg-brand-50/50 p-5 sm:p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-brand-950">{activeSection.label} details</h2>
                <button type="button" onClick={() => setViewingItem(null)} className="btn-icon" aria-label="Close details">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {config.fields.map(([name, label, type]) => (
                  <div key={name} className={type === 'textarea' ? 'sm:col-span-2' : ''}>
                    <dt className="text-xs font-semibold uppercase tracking-wide text-brand-500">{label}</dt>
                    <dd className="mt-1 whitespace-pre-wrap break-words text-sm text-slate-800">{viewingItem[name] || 'Not provided'}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-brand-950">{activeSection.label}</h2>
            {!isLoading && <span className="rounded-full bg-brand-100 px-2.5 py-0.5 text-xs font-semibold text-brand-700">{items.length}</span>}
          </div>

          {isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {[0, 1].map((key) => <div key={key} className="h-32 animate-pulse rounded-2xl border border-brand-100 bg-brand-50" />)}
            </div>
          ) : items.length === 0 ? (
            <div className="card flex flex-col items-center px-6 py-14 text-center">
              <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-500">
                <ActiveIcon className="h-7 w-7" />
              </span>
              <p className="font-semibold text-brand-950">No {activeSection.label.toLowerCase()} yet</p>
              <p className="mt-1 text-sm text-slate-500">Add your first entry to start building your profile.</p>
              <button onClick={openForm} className="btn-primary mt-5">
                <Plus className="h-4 w-4" /> Add {activeSection.singular}
              </button>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {items.map((item) => (
                <article key={item.id} className="card flex flex-col p-5 transition hover:border-brand-300 hover:shadow-md">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="break-words font-semibold text-brand-950">{item.name || item.course_name || item.company_name || item.certificate_name || item.description}</h3>
                      {(item.role || item.college_name || item.certificate_issuer) && (
                        <p className="mt-0.5 text-sm text-brand-600">{item.role || item.college_name || item.certificate_issuer}</p>
                      )}
                    </div>
                    <div className="-mr-2 -mt-1 flex shrink-0 items-center">
                      <button type="button" onClick={() => setViewingItem(item)} title="View" aria-label="View item" className="btn-icon">
                        <Eye className="h-4 w-4" />
                      </button>
                      <button type="button" onClick={() => openEditForm(item)} title="Edit" aria-label="Edit item" className="btn-icon">
                        <Edit3 className="h-4 w-4" />
                      </button>
                      <button type="button" onClick={() => handleDelete(item)} title="Delete" aria-label="Delete item" className="btn-icon hover:bg-red-50 hover:text-red-600">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  {item.description && item.name && <p className="mt-2 line-clamp-3 text-sm text-slate-600">{item.description}</p>}
                  {item.tech_stack && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {item.tech_stack.split(',').map((tech) => tech.trim()).filter(Boolean).map((tech) => (
                        <span key={tech} className="rounded-md bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">{tech}</span>
                      ))}
                    </div>
                  )}
                  {(item.duration || item.start_year) && (
                    <p className="mt-auto pt-3 text-xs text-slate-500">{item.duration || `${item.start_year} – ${item.end_year}`}</p>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default CRUD;
