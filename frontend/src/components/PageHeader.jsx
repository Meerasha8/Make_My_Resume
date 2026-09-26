import React from 'react';

const PageHeader = ({ icon: Icon, title, subtitle, actions }) => (
  <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <div className="flex items-center gap-3">
      {Icon && (
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-md shadow-brand-600/25">
          <Icon className="h-5 w-5" />
        </span>
      )}
      <div>
        <h1 className="text-xl font-bold text-brand-950 sm:text-2xl">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>
    </div>
    {actions && <div className="flex shrink-0 gap-2">{actions}</div>}
  </div>
);

export default PageHeader;
