import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import Keycloak from 'keycloak-js';
import ThemeSwitcher from './ThemeSwitcher';

const KEYCLOAK_CONFIG = { url: 'https://auth.makotools.ru', realm: 'MAKO', clientId: 'ai-platform' };
const API_BASE = window.location.origin;
const AUTH_URL = `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/auth`;
const TOKEN_URL = `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`;
const REDIRECT_URI = `${window.location.origin}/login-callback.html`;

interface AgentInfo { name: string; display_name: string; category: string; model_name: string; schema_type: string; is_active: boolean; }
interface ModelSummary { model: string; count: number; }
interface ReviewerModelSummary { model: string; count: number; }
interface SystemModel { role: string; model: string; description: string; }
interface CategorySummary { category: string; count: number; }
interface ServiceStatus { name: string; status: string; }

interface DashboardData {
  agents: AgentInfo[];
  agents_total: number;
  agents_active: number;
  models?: ModelSummary[];
  reviewer_models?: ReviewerModelSummary[];
  system_models?: SystemModel[];
  categories: CategorySummary[];
  services: ServiceStatus[];
  database: { status: string };
  llm: { provider: string; base_url: string };
  memory: { status: string; note: string };
  monitoring: { status: string; note: string };
}

const CATEGORY_LABELS: Record<string, string> = {
  management: 'Управление', research: 'Исследования', architecture: 'Архитектура',
  development: 'Разработка', business: 'Бизнес', content: 'Контент',
  support: 'Поддержка', ai_ops: 'AI Ops',
};

const base64URLEncode = (buffer: Uint8Array) =>
  btoa(String.fromCharCode(...buffer)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

const generateCodeVerifier = () => {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64URLEncode(array);
};

const generateCodeChallenge = async (verifier: string) => {
  const data = new TextEncoder().encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return base64URLEncode(new Uint8Array(digest));
};

const Dashboard: React.FC = () => {
  const [keycloak, setKeycloak] = useState<Keycloak | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [roles, setRoles] = useState<string[]>([]);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [iframeSrc, setIframeSrc] = useState('');
  const codeVerifierRef = useRef('');

  useEffect(() => {
    const kc = new Keycloak(KEYCLOAK_CONFIG);
    kc.init({ onLoad: 'check-sso', pkceMethod: 'S256', silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html' })
      .then((auth) => {
        setKeycloak(kc);
        if (auth) {
          setAuthenticated(true);
          setUsername(kc.tokenParsed?.preferred_username || kc.tokenParsed?.name || 'User');
          setRoles(kc.tokenParsed?.realm_access?.roles || []);
        }
      })
      .catch((err) => console.error('Keycloak init:', err));
  }, []);

  useEffect(() => {
    const handler = async (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === 'kc-auth-success' && event.data.code) {
        setShowLoginModal(false);
        try {
          const params = new URLSearchParams({
            grant_type: 'authorization_code',
            client_id: KEYCLOAK_CONFIG.clientId,
            code: event.data.code,
            code_verifier: codeVerifierRef.current,
            redirect_uri: REDIRECT_URI,
          });
          const res = await fetch(TOKEN_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params,
          });
          const tokenData = await res.json();
          if (tokenData.access_token) {
            const payload = JSON.parse(atob(tokenData.access_token.split('.')[1]));
            setAuthenticated(true);
            setUsername(payload.preferred_username || payload.name || 'User');
            setRoles(payload.realm_access?.roles || []);
            localStorage.setItem('mako_token', tokenData.access_token);
            localStorage.setItem('mako_refresh_token', tokenData.refresh_token || '');
          }
        } catch (err) { console.error('Token exchange error:', err); }
      }
      if (event.data?.type === 'kc-auth-error') {
        setShowLoginModal(false);
        console.error('Auth error:', event.data.error);
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/v1/dashboard/status`);
      if (res.ok) setData(await res.json());
    } catch (e) { console.error('Dashboard fetch error:', e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleLogin = async () => {
    const verifier = generateCodeVerifier();
    codeVerifierRef.current = verifier;
    const challenge = await generateCodeChallenge(verifier);
    const params = new URLSearchParams({
      client_id: KEYCLOAK_CONFIG.clientId,
      redirect_uri: REDIRECT_URI,
      response_type: 'code',
      scope: 'openid profile email',
      code_challenge: challenge,
      code_challenge_method: 'S256',
      prompt: 'login',
    });
    setIframeSrc(`${AUTH_URL}?${params.toString()}`);
    setShowLoginModal(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('mako_token');
    localStorage.removeItem('mako_refresh_token');
    setAuthenticated(false);
    setUsername('');
    setRoles([]);
    keycloak?.logout({ redirectUri: window.location.origin }).catch(() => {});
  };

  const hasRole = (role: string) => roles.includes(role);

  const StatusDot = ({ status }: { status: string }) => {
    const colors: Record<string, string> = { up: 'var(--status-online)', down: 'var(--status-offline)', not_connected: 'var(--status-warning)', not_configured: 'var(--status-neutral)' };
    const labels: Record<string, string> = { up: 'Online', down: 'Offline', not_connected: 'Не подключено', not_configured: 'Не настроено' };
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: colors[status] || 'var(--status-neutral)' }} />
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col relative transition-colors duration-300">
      {showLoginModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/75 animate-fadeIn" onClick={() => setShowLoginModal(false)}>
          <div className="relative w-[95vw] max-w-[440px] h-[80vh] max-h-[600px] rounded-2xl overflow-hidden border border-[var(--border-primary)] bg-[var(--bg-card)] shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <button onClick={() => setShowLoginModal(false)}
              className="absolute top-3 right-3 z-10 w-8 h-8 rounded-full bg-[var(--bg-button)] text-[var(--text-primary)] flex items-center justify-center hover:bg-[var(--bg-button-hover)] transition-colors">
              <i className="fa-solid fa-xmark text-sm" />
            </button>
            <iframe src={iframeSrc} className="w-full h-full border-none" title="MAKO Login" />
          </div>
        </div>
      )}

      <div className="fixed top-3 right-3 sm:top-5 sm:right-6 z-50 flex items-center gap-2 sm:gap-3">
        <ThemeSwitcher />
        {authenticated ? (
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden sm:flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-full bg-[var(--bg-button)] flex items-center justify-center border border-[var(--border-primary)]">
                <i className="fa-solid fa-user text-[var(--text-primary)] text-xs" />
              </div>
              <span className="text-[var(--text-primary)] text-sm font-medium">{username}</span>
            </div>
            <button onClick={handleLogout} className="px-3 sm:px-5 py-2 sm:py-2.5 bg-[var(--bg-button)]/50 text-[var(--text-primary)] rounded-lg text-xs sm:text-sm hover:bg-[var(--bg-button)] transition-colors border border-[var(--border-primary)]">
              <i className="fa-solid fa-right-from-bracket sm:mr-2" /><span className="hidden sm:inline">Выйти</span>
            </button>
          </div>
        ) : (
          <button onClick={handleLogin} className="px-5 sm:px-8 py-3 sm:py-4 bg-[var(--bg-button)] text-[var(--text-primary)] rounded-xl text-sm sm:text-lg font-semibold hover:bg-[var(--bg-button-hover)] hover:scale-105 transition-all shadow-lg border border-[var(--border-hover)]">
            <i className="fa-solid fa-right-to-bracket sm:mr-3" /><span className="hidden sm:inline">Войти</span>
          </button>
        )}
      </div>

      <div className="flex justify-center items-start pt-8 sm:pt-10">
        <img src="/static/images/makogroup-logo-420-140.png" alt="MAKO AI Ecosystem" className="h-[10vh] sm:h-[15vh] opacity-0 animate-fadeInLogo" style={{ animationDuration: '3s' }} />
      </div>

      <div className="flex justify-center mt-4 sm:mt-6 px-4 animate-fadeInUp delay-1500">
        <div className="text-center">
          <h1 className="text-xl sm:text-3xl font-bold text-[var(--text-primary)] tracking-widest uppercase">Agent Runtime</h1>
          <p className="text-sm sm:text-base text-[var(--text-secondary)] mt-1 sm:mt-2 tracking-wide">A part of MAKO AI Ecosystem</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row justify-center items-center gap-4 sm:gap-8 mt-8 sm:mt-12 px-4 animate-fadeInUp delay-2000">
        {(!authenticated || hasRole('agents-admin')) && (
          <Link to={authenticated ? '/admin' : '#'} onClick={(e) => { if (!authenticated) { e.preventDefault(); handleLogin(); } }}
            className="group w-full sm:w-auto px-8 sm:px-12 py-6 sm:py-8 bg-[var(--bg-button)]/30 border-2 border-[var(--border-primary)] rounded-2xl text-center hover:bg-[var(--bg-button)]/60 hover:border-[var(--border-hover)] hover:scale-105 transition-all shadow-xl sm:min-w-[240px]">
            <i className="fa-solid fa-user-shield text-3xl sm:text-4xl text-[var(--text-primary)] mb-3 sm:mb-4 block group-hover:scale-110 transition-transform" />
            <span className="text-[var(--text-primary)] text-lg sm:text-xl font-bold block">Agents Admin</span>
            <span className="text-[var(--text-muted)] text-xs sm:text-sm mt-1 sm:mt-2 block">Управление агентами</span>
          </Link>
        )}
        {(!authenticated || hasRole('agents-runtime')) && (
          <Link to={authenticated ? '/chat' : '#'} onClick={(e) => { if (!authenticated) { e.preventDefault(); handleLogin(); } }}
            className="group w-full sm:w-auto px-8 sm:px-12 py-6 sm:py-8 bg-[var(--bg-button)]/30 border-2 border-[var(--border-primary)] rounded-2xl text-center hover:bg-[var(--bg-button)]/60 hover:border-[var(--border-hover)] hover:scale-105 transition-all shadow-xl sm:min-w-[240px]">
            <i className="fa-solid fa-robot text-3xl sm:text-4xl text-[var(--text-primary)] mb-3 sm:mb-4 block group-hover:scale-110 transition-transform" />
            <span className="text-[var(--text-primary)] text-lg sm:text-xl font-bold block">Agents Runtime</span>
            <span className="text-[var(--text-muted)] text-xs sm:text-sm mt-1 sm:mt-2 block">Запуск и диалог</span>
          </Link>
        )}
    {/* Diagram Studio — ВСЕГДА видима, без ролевой проверки */}
          <Link
            to="/diagram-studio"
            className="group w-full sm:w-auto px-8 sm:px-12 py-6 sm:py-8 bg-[var(--bg-button)]/30 border-2 border-[var(--border-primary)] rounded-2xl text-center hover:bg-[var(--bg-button)]/60 hover:border-[var(--border-hover)] hover:scale-105 transition-all shadow-xl sm:min-w-[240px]"
          >
            <i className="fa-solid fa-diagram-project text-3xl sm:text-4xl text-[var(--text-primary)] mb-3 sm:mb-4 block group-hover:scale-110 transition-transform" />
            <span className="text-[var(--text-primary)] text-lg sm:text-xl font-bold block">Diagram Studio</span>
            <span className="text-[var(--text-muted)] text-xs sm:text-sm mt-1 sm:mt-2 block">Mermaid-диаграммы + PDF</span>
          </Link>
      </div>

      <main className="flex-1 flex justify-center p-4 sm:p-8 mt-6 sm:mt-10 animate-fadeInUp delay-2500">
        <div className="flex flex-wrap gap-4 sm:gap-5 justify-center max-w-[920px] w-full">

          {/* Агенты */}
          <div className="w-full sm:w-[280px] bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl p-4 sm:p-5 hover:border-[var(--border-hover)] transition-colors">
            <div className="flex items-center gap-3 mb-3 sm:mb-4">
              <i className="fa-solid fa-robot text-lg sm:text-xl text-[var(--text-primary)]" />
              <h3 className="text-[var(--text-primary)] font-bold text-xs sm:text-sm uppercase tracking-wide">Агенты</h3>
            </div>
            {loading ? <p className="text-[var(--text-muted)] text-xs">Загрузка...</p> : data ? (
              <div className="space-y-1.5 text-xs text-[var(--text-secondary)]">
                <p>Всего: <span className="text-[var(--text-primary)] font-bold">{data.agents_total}</span></p>
                <p>Активных: <span className="text-[var(--text-primary)] font-bold">{data.agents_active}</span></p>
                <div className="mt-2 sm:mt-3 space-y-1 border-t border-[var(--border-primary)] pt-2">
                  {(data.categories || []).map((c) => (
                    <div key={c.category} className="flex justify-between">
                      <span>{CATEGORY_LABELS[c.category] || c.category}</span>
                      <span className="text-[var(--text-primary)] font-medium">{c.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : <p className="text-[var(--text-muted)] text-xs">Нет данных</p>}
          </div>

          {/* LLM */}
          <div className="w-full sm:w-[280px] bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl p-4 sm:p-5 hover:border-[var(--border-hover)] transition-colors">
            <div className="flex items-center gap-3 mb-3 sm:mb-4">
              <i className="fa-solid fa-brain text-lg sm:text-xl text-[var(--text-primary)]" />
              <h3 className="text-[var(--text-primary)] font-bold text-xs sm:text-sm uppercase tracking-wide">LLM</h3>
            </div>
            {loading ? <p className="text-[var(--text-muted)] text-xs">Загрузка...</p> : data ? (
              <div className="space-y-1.5 text-xs text-[var(--text-secondary)]">
                <p>Провайдер: <span className="text-[var(--text-primary)] font-bold">{data.llm?.provider || 'N/A'}</span></p>

                {/* Агентские */}
                <div className="mt-2 sm:mt-3 space-y-1 border-t border-[var(--border-primary)] pt-2">
                  <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                    <i className="fa-solid fa-robot mr-1" />Агентские
                  </p>
                  {(!data.models || data.models.length === 0) ? (
                    <p className="text-[var(--text-muted)]">Нет данных</p>
                  ) : (
                    data.models.map((m) => (
                      <div key={m.model} className="flex justify-between">
                        <span className="truncate mr-2">{m.model}</span>
                        <span className="text-[var(--text-primary)] whitespace-nowrap">{m.count} аг.</span>
                      </div>
                    ))
                  )}
                </div>

                {/* Ревьюерские */}
                {data.reviewer_models && data.reviewer_models.length > 0 && (
                  <div className="mt-2 sm:mt-3 space-y-1 border-t border-[var(--border-primary)] pt-2">
                    <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                      <i className="fa-solid fa-clipboard-check mr-1" />Ревьюерские
                    </p>
                    {data.reviewer_models.map((m) => (
                      <div key={m.model} className="flex justify-between">
                        <span className="truncate mr-2">{m.model}</span>
                        <span className="text-[var(--text-primary)] whitespace-nowrap">{m.count} аг.</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Системные */}
                {data.system_models && data.system_models.length > 0 && (
                  <div className="mt-2 sm:mt-3 space-y-1 border-t border-[var(--border-primary)] pt-2">
                    <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                      <i className="fa-solid fa-gear mr-1" />Системные
                    </p>
                    {data.system_models.map((sm) => (
                      <div key={sm.role} className="flex justify-between items-center" title={sm.description}>
                        <span className="text-[var(--text-muted)] font-medium shrink-0 w-20">{sm.role}</span>
                        <span className="text-[var(--text-primary)] font-mono text-[10px] truncate ml-1" title={sm.model}>
                          {sm.model.replace(/^[^/]+\//, '')}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : <p className="text-[var(--text-muted)] text-xs">Нет данных</p>}
          </div>

          {/* Сервисы */}
          <div className="w-full sm:w-[280px] bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl p-4 sm:p-5 hover:border-[var(--border-hover)] transition-colors">
            <div className="flex items-center gap-3 mb-3 sm:mb-4">
              <i className="fa-solid fa-server text-lg sm:text-xl text-[var(--text-primary)]" />
              <h3 className="text-[var(--text-primary)] font-bold text-xs sm:text-sm uppercase tracking-wide">Сервисы</h3>
            </div>
            {loading ? <p className="text-[var(--text-muted)] text-xs">Загрузка...</p> : data ? (
              <div className="space-y-2 text-xs">
                {(data.services || []).map((s) => (
                  <div key={s.name} className="flex justify-between items-center">
                    <span className="text-[var(--text-secondary)]">{s.name}</span>
                    <StatusDot status={s.status} />
                  </div>
                ))}
              </div>
            ) : <p className="text-[var(--text-muted)] text-xs">Нет данных</p>}
          </div>

          {/* RAG */}
          <div className="w-full sm:w-[280px] bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl p-4 sm:p-5 hover:border-[var(--border-hover)] transition-colors">
            <div className="flex items-center gap-3 mb-3 sm:mb-4">
              <i className="fa-solid fa-magnifying-glass text-lg sm:text-xl text-[var(--text-primary)]" />
              <h3 className="text-[var(--text-primary)] font-bold text-xs sm:text-sm uppercase tracking-wide">RAG</h3>
            </div>
            {loading ? <p className="text-[var(--text-muted)] text-xs">Загрузка...</p> : data ? (
              <div className="space-y-2 text-xs text-[var(--text-secondary)]">
                <p>RAGFlow: <StatusDot status={data.services?.find(s => s.name === 'RAGFlow')?.status || 'down'} /></p>
                <p className="text-[var(--text-muted)] mt-2">Датасеты: подключение в процессе</p>
              </div>
            ) : <p className="text-[var(--text-muted)] text-xs">Нет данных</p>}
          </div>

          {/* Память */}
          <div className="w-full sm:w-[280px] bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl p-4 sm:p-5 hover:border-[var(--border-hover)] transition-colors">
            <div className="flex items-center gap-3 mb-3 sm:mb-4">
              <i className="fa-solid fa-memory text-lg sm:text-xl text-[var(--text-primary)]" />
              <h3 className="text-[var(--text-primary)] font-bold text-xs sm:text-sm uppercase tracking-wide">Память</h3>
            </div>
            {loading ? <p className="text-[var(--text-muted)] text-xs">Загрузка...</p> : data ? (
              <div className="space-y-2 text-xs text-[var(--text-secondary)]">
                <p>pgvector: <StatusDot status={data.memory?.status || 'not_connected'} /></p>
                <p className="text-[var(--text-muted)]">{data.memory?.note || ''}</p>
              </div>
            ) : <p className="text-[var(--text-muted)] text-xs">Нет данных</p>}
          </div>

          {/* Мониторинг */}
          <div className="w-full sm:w-[280px] bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl p-4 sm:p-5 hover:border-[var(--border-hover)] transition-colors">
            <div className="flex items-center gap-3 mb-3 sm:mb-4">
              <i className="fa-solid fa-chart-line text-lg sm:text-xl text-[var(--text-primary)]" />
              <h3 className="text-[var(--text-primary)] font-bold text-xs sm:text-sm uppercase tracking-wide">Мониторинг</h3>
            </div>
            {loading ? <p className="text-[var(--text-muted)] text-xs">Загрузка...</p> : data ? (
              <div className="space-y-2 text-xs text-[var(--text-secondary)]">
                <p>Статус: <StatusDot status={data.monitoring?.status || 'not_configured'} /></p>
                <p className="text-[var(--text-muted)]">{data.monitoring?.note || ''}</p>
              </div>
            ) : <p className="text-[var(--text-muted)] text-xs">Нет данных</p>}
          </div>

        </div>
      </main>
    </div>
  );
};

export default Dashboard;