import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, FileText, Settings, LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'AI Chat', path: '/chatbot', icon: MessageSquare },
  { name: 'Resume', path: '/resume', icon: FileText },
  { name: 'Settings', path: '/settings', icon: Settings },
];

const linkClass = ({ isActive }) =>
  `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/25' : 'text-slate-600 hover:bg-brand-50 hover:text-brand-700'
  }`;

const Navbar = () => {
  const { logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const closeMenu = () => setIsMenuOpen(false);

  return (
    <header className="sticky top-0 z-30 border-b border-brand-100 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <NavLink to="/" onClick={closeMenu}>
          <Logo />
        </NavLink>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.path} to={item.path} end className={linkClass}>
              <item.icon className="h-4 w-4" />
              {item.name}
            </NavLink>
          ))}
        </nav>

        <button onClick={logout} className="btn-secondary hidden md:inline-flex">
          <LogOut className="h-4 w-4" />
          Sign out
        </button>

        <button
          type="button"
          onClick={() => setIsMenuOpen((open) => !open)}
          className="btn-icon md:hidden"
          aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={isMenuOpen}
        >
          {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {isMenuOpen && (
        <nav className="space-y-1 border-t border-brand-100 bg-white px-4 py-3 md:hidden">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.path} to={item.path} end className={linkClass} onClick={closeMenu}>
              <item.icon className="h-4 w-4" />
              {item.name}
            </NavLink>
          ))}
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </nav>
      )}
    </header>
  );
};

export default Navbar;
