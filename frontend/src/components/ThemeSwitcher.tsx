import React, { useState, useEffect, useRef } from 'react';

const THEMES = [
  { id: 'root', label: 'MAKO Default' },
  { id: 'ocean-dark', label: 'Ocean Dark' },
  { id: 'moody-sunset', label: 'Moody Sunset' },
  { id: 'forest-breeze', label: 'Forest Breeze' },
  { id: 'clay-and-sea', label: 'Clay and Sea' },
  { id: 'viewing', label: 'Viewing' },
  { id: 'blue-tone', label: 'Blue Tone' },
];

const STORAGE_KEY = 'mako_theme';

const ThemeSwitcher: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem(STORAGE_KEY) || 'root');
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (theme === 'root') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', theme);
    }
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-10 h-10 rounded-lg bg-[var(--bg-button)] text-[var(--text-primary)] flex items-center justify-center hover:bg-[var(--bg-button-hover)] transition-colors border border-[var(--border-primary)]"
        title="Палитра"
      >
        <i className="fa-solid fa-palette text-sm" />
      </button>
      {open && (
        <div className="absolute right-0 top-12 w-48 bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl shadow-xl overflow-hidden z-[200]">
          {THEMES.map((t) => (
            <button
              key={t.id}
              onClick={() => { setTheme(t.id); setOpen(false); }}
              className={`w-full px-4 py-2.5 text-left text-sm transition-colors flex items-center justify-between ${
                theme === t.id
                  ? 'bg-[var(--bg-button)] text-[var(--text-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-button)]/30 hover:text-[var(--text-primary)]'
              }`}
            >
              {t.label}
              {theme === t.id && <i className="fa-solid fa-check text-xs" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ThemeSwitcher;