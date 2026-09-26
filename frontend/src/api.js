// Production (Vercel): set VITE_API_BASE_URL to the Render backend URL, e.g. https://make-my-resume-api.onrender.com
// Docker all-in-one: leave it unset; the API is served from the same origin, so the base URL is relative.
// `npm run dev`: defaults to the API on http://localhost:8000.
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://localhost:8000' : '')
).replace(/\/+$/, '');
