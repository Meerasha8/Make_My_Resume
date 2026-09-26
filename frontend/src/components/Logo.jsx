import React from 'react';
import { FileText } from 'lucide-react';

const Logo = ({ inverted = false, className = '' }) => (
  <div className={`flex items-center gap-2.5 ${className}`}>
    <span
      className={`flex h-9 w-9 items-center justify-center rounded-xl ${
        inverted ? 'bg-white text-brand-700' : 'bg-gradient-to-br from-brand-500 to-brand-800 text-white shadow-md shadow-brand-600/30'
      }`}
    >
      <FileText className="h-5 w-5" />
    </span>
    <span className={`text-lg font-extrabold tracking-tight ${inverted ? 'text-white' : 'text-brand-950'}`}>
      Make My <span className={inverted ? 'text-brand-200' : 'text-brand-600'}>Resume</span>
    </span>
  </div>
);

export default Logo;
