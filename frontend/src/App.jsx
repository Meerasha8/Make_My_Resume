import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import CRUD from './pages/CRUD';
import AIChatbot from './pages/AIChatbot';
import Resume from './pages/Resume';
import Settings from './pages/Settings';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import { useAuth } from './context/AuthContext';

function App() {
  const { token } = useAuth();

  return (
    <div className="flex min-h-screen flex-col">
      {token && <Navbar />}
      <main className={token ? 'mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-10' : 'flex-1'}>
        <Routes>
          <Route path="/login" element={!token ? <Login /> : <Navigate to="/" />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<CRUD />} />
            <Route path="/chatbot" element={<AIChatbot />} />
            <Route path="/resume" element={<Resume />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
      </main>
    </div>
  );
}

export default App;
