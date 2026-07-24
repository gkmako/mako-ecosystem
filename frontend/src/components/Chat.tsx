import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import mermaid from 'mermaid';
import ThemeSwitcher from './ThemeSwitcher';

mermaid.initialize({ startOnLoad: false, theme: 'dark', themeVariables: { primaryColor: '#336649', primaryTextColor: '#b5e3d8', lineColor: '#b5e3d8' } });

interface Message { id: string; role: 'user' | 'assistant'; content: string; timestamp: number; }
interface Conversation { id: string; title: string; messages: Message[]; createdAt: number; updatedAt: number; pinned?: boolean; }
interface TTSSettings { voice: string; speed: number; autoPlay: boolean; }

const STORAGE_KEY = 'mako_chat_conversations';
const TTS_SETTINGS_KEY = 'mako_tts_settings';
const isMobile = () => window.innerWidth < 768;
const loadConversations = (): Conversation[] => { try { const r = localStorage.getItem(STORAGE_KEY); return r ? JSON.parse(r) : []; } catch { return []; } };
const saveConversations = (c: Conversation[]) => { localStorage.setItem(STORAGE_KEY, JSON.stringify(c)); };
const loadTTSSettings = (): TTSSettings => { try { const r = localStorage.getItem(TTS_SETTINGS_KEY); return r ? JSON.parse(r) : { voice: 'eve', speed: 1.0, autoPlay: false }; } catch { return { voice: 'eve', speed: 1.0, autoPlay: false }; } };

const TTS_VOICES = [
  { id: 'eve', label: 'Eve (женский, мягкий)' },
  { id: 'ara', label: 'Ara (женский, энергичный)' },
  { id: 'rex', label: 'Rex (мужской, уверенный)' },
  { id: 'sal', label: 'Sal (мужской, спокойный)' },
  { id: 'leo', label: 'Leo (мужской, тёплый)' },
];

const MermaidBlock: React.FC<{ code: string }> = ({ code }) => {
  const [svg, setSvg] = useState('');
  useEffect(() => {
    const id = `mermaid-${Math.random().toString(36).slice(2)}`;
    mermaid.render(id, code).then(({ svg }) => setSvg(svg)).catch(() => setSvg(''));
  }, [code]);
  if (!svg) return <pre className="text-xs text-[var(--text-muted)] p-3 bg-[var(--bg-primary)] rounded-lg overflow-x-auto">{code}</pre>;
  return <div className="mermaid-container my-3 flex justify-center" dangerouslySetInnerHTML={{ __html: svg }} />;
};

const MarkdownContent: React.FC<{ content: string }> = ({ content }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
    code({ className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      const lang = match ? match[1] : '';
      const codeStr = String(children).replace(/\n$/, '');
      if (lang === 'mermaid') return <MermaidBlock code={codeStr} />;
      return <code className={`${className || ''} text-sm bg-[var(--bg-primary)] px-1.5 py-0.5 rounded text-[var(--text-primary)]`} {...props}>{children}</code>;
    },
    pre({ children }) { return <pre className="my-3 p-3 sm:p-4 bg-[var(--bg-primary)] rounded-lg overflow-x-auto border border-[var(--border-primary)]">{children}</pre>; },
    table({ children }) { return <div className="overflow-x-auto my-3"><table className="min-w-full text-sm border-collapse border border-[var(--border-primary)]">{children}</table></div>; },
    th({ children }) { return <th className="border border-[var(--border-primary)] px-3 py-2 bg-[var(--bg-button)]/20 text-[var(--text-primary)] font-semibold text-left">{children}</th>; },
    td({ children }) { return <td className="border border-[var(--border-primary)] px-3 py-2 text-[var(--text-secondary)]">{children}</td>; },
    a({ href, children }) { return <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--text-primary)] underline hover:opacity-80">{children}</a>; },
    p({ children }) { return <p className="my-2 leading-relaxed">{children}</p>; },
    ul({ children }) { return <ul className="my-2 ml-5 list-disc space-y-1">{children}</ul>; },
    ol({ children }) { return <ol className="my-2 ml-5 list-decimal space-y-1">{children}</ol>; },
    blockquote({ children }) { return <blockquote className="my-3 pl-4 border-l-2 border-[var(--accent)] text-[var(--text-secondary)] italic">{children}</blockquote>; },
    h1({ children }) { return <h1 className="text-xl font-bold mt-4 mb-2 text-[var(--text-primary)]">{children}</h1>; },
    h2({ children }) { return <h2 className="text-lg font-bold mt-3 mb-2 text-[var(--text-primary)]">{children}</h2>; },
    h3({ children }) { return <h3 className="text-base font-bold mt-3 mb-1 text-[var(--text-primary)]">{children}</h3>; },
  }}>{content}</ReactMarkdown>
);

const Chat: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>(loadConversations);
  const [activeId, setActiveId] = useState<string | null>(conversations[0]?.id || null);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(() => !isMobile());
  const [listening, setListening] = useState(false);
  const [menuId, setMenuId] = useState<string | null>(null);
  const [renameId, setRenameId] = useState<string | null>(null);
  const [renameText, setRenameText] = useState('');
  const [ttsSettings, setTtsSettings] = useState<TTSSettings>(loadTTSSettings);
  const [showTtsSettings, setShowTtsSettings] = useState(false);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [currentStatus, setCurrentStatus] = useState('Готов к работе');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const ttsMenuRef = useRef<HTMLDivElement>(null);

  const activeConv = conversations.find((c) => c.id === activeId) || null;
  const sortedConvs = [...conversations].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    return b.updatedAt - a.updatedAt;
  });

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [activeConv?.messages]);
  useEffect(() => { saveConversations(conversations); }, [conversations]);
  useEffect(() => { localStorage.setItem(TTS_SETTINGS_KEY, JSON.stringify(ttsSettings)); }, [ttsSettings]);
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuId(null);
      if (ttsMenuRef.current && !ttsMenuRef.current.contains(e.target as Node)) setShowTtsSettings(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const playTTS = async (text: string, msgId: string) => {
    if (playingId === msgId) { audioRef.current?.pause(); setPlayingId(null); return; }
    audioRef.current?.pause();
    setPlayingId(msgId);
    try {
      const res = await fetch(`${window.location.origin}/v1/audio/speech`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: text, voice: ttsSettings.voice, response_format: 'mp3' }),
      });
      if (!res.ok) throw new Error(`TTS HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { setPlayingId(null); URL.revokeObjectURL(url); };
      audio.onerror = () => { setPlayingId(null); URL.revokeObjectURL(url); };
      await audio.play();
    } catch (err) { console.error('TTS error:', err); setPlayingId(null); }
  };

  const toggleVoice = async () => {
    if (listening) { mediaRecorderRef.current?.stop(); setListening(false); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        try {
          const formData = new FormData();
          formData.append('file', blob, 'recording.webm');
          const res = await fetch(`${window.location.origin}/v1/audio/transcriptions`, { method: 'POST', body: formData });
          if (res.ok) {
            const data = await res.json();
            const text = data.text || data.choices?.[0]?.text || '';
            if (text) setInput((prev) => prev + text);
          } else { console.error('STT error:', res.status); }
        } catch (err) { console.error('STT error:', err); }
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setListening(true);
    } catch (err) { console.error('Mic error:', err); alert('Нет доступа к микрофону'); }
  };

  const createConversation = () => {
    const conv: Conversation = { id: crypto.randomUUID(), title: 'Новый диалог', messages: [], createdAt: Date.now(), updatedAt: Date.now() };
    setConversations((p) => [conv, ...p]);
    setActiveId(conv.id);
    setInput('');
    if (isMobile()) setSidebarOpen(false);
    inputRef.current?.focus();
  };

  const selectConversation = (id: string) => {
    setActiveId(id);
    if (isMobile()) setSidebarOpen(false);
  };

  const deleteConversation = (id: string) => {
    setConversations((p) => { const u = p.filter((c) => c.id !== id); if (activeId === id) setActiveId(u[0]?.id || null); return u; });
    setMenuId(null);
  };

  const togglePin = (id: string) => {
    setConversations((p) => p.map((c) => c.id === id ? { ...c, pinned: !c.pinned } : c));
    setMenuId(null);
  };

  const startRename = (id: string, title: string) => { setRenameId(id); setRenameText(title); setMenuId(null); };
  const confirmRename = () => {
    if (renameId && renameText.trim()) setConversations((p) => p.map((c) => c.id === renameId ? { ...c, title: renameText.trim() } : c));
    setRenameId(null); setRenameText('');
  };

  const downloadConversation = (id: string) => {
    const conv = conversations.find((c) => c.id === id);
    if (!conv) return;
    let md = `# ${conv.title}\n\n`;
    conv.messages.forEach((m) => { md += `## ${m.role === 'user' ? '👤 Вы' : '🤖 Ассистент'}\n\n${m.content}\n\n---\n\n`; });
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `${conv.title.replace(/[^a-zA-Zа-яА-Я0-9]/g, '_')}.md`; a.click();
    URL.revokeObjectURL(url); setMenuId(null);
  };

  const sendMessage = useCallback(async (text?: string) => {
    const msgText = (text || input).trim();
    if (!msgText || streaming) return;
    let convId = activeId;
    if (!convId) {
      const conv: Conversation = { id: crypto.randomUUID(), title: msgText.slice(0, 50) + (msgText.length > 50 ? '...' : ''), messages: [], createdAt: Date.now(), updatedAt: Date.now() };
      setConversations((p) => [conv, ...p]); setActiveId(conv.id); convId = conv.id;
    }
    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: msgText, timestamp: Date.now() };
    const assistantMsg: Message = { id: crypto.randomUUID(), role: 'assistant', content: '', timestamp: Date.now() };
    setConversations((p) => p.map((c) => {
      if (c.id !== convId) return c;
      const title = c.messages.length === 0 ? msgText.slice(0, 50) + (msgText.length > 50 ? '...' : '') : c.title;
      return { ...c, title, messages: [...c.messages, userMsg, assistantMsg], updatedAt: Date.now() };
    }));
    setInput(''); setStreaming(true);
    setCurrentStatus('Отправка запроса...');

    const currentConv = conversations.find((c) => c.id === convId);
    const apiMessages = [...(currentConv?.messages || []).map((m) => ({ role: m.role, content: m.content })), { role: 'user' as const, content: msgText }];
    let fullResponse = '';
    try {
      const res = await fetch(`${window.location.origin}/v1/chat/completions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: 'makotools', messages: apiMessages, stream: true, user: convId }),
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader(); const decoder = new TextDecoder(); let buffer = '';
      while (true) {
        const { done, value } = await reader.read(); if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n'); buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6).trim(); if (data === '[DONE]') continue;
          try {
            const parsed = JSON.parse(data);
            if (parsed.type === 'metadata') continue;
            if (parsed.type === 'status') {
              setCurrentStatus(parsed.status);
              continue;
            }
            const delta = parsed.choices?.[0]?.delta?.content;
            if (delta) {
              fullResponse += delta;
              setConversations((p) => p.map((c) => {
                if (c.id !== convId) return c;
                const msgs = [...c.messages]; const last = msgs[msgs.length - 1];
                if (last && last.role === 'assistant') msgs[msgs.length - 1] = { ...last, content: last.content + delta };
                return { ...c, messages: msgs, updatedAt: Date.now() };
              }));
            }
          } catch { /* skip */ }
        }
      }
      if (ttsSettings.autoPlay && fullResponse) playTTS(fullResponse, assistantMsg.id);
    } catch (err) {
      setConversations((p) => p.map((c) => {
        if (c.id !== convId) return c;
        const msgs = [...c.messages]; const last = msgs[msgs.length - 1];
        if (last && last.role === 'assistant' && !last.content) msgs[msgs.length - 1] = { ...last, content: `⚠️ Ошибка: ${err instanceof Error ? err.message : 'Unknown'}` };
        return { ...c, messages: msgs };
      }));
    } finally {
      setStreaming(false);
      setCurrentStatus('Готов к работе');
    }
  }, [input, streaming, activeId, conversations, ttsSettings]);

  const retryLast = () => {
    if (!activeConv || streaming) return;
    const lastUser = [...activeConv.messages].reverse().find((m) => m.role === 'user');
    if (!lastUser) return;
    setConversations((p) => p.map((c) => {
      if (c.id !== activeId) return c;
      const msgs = [...c.messages]; if (msgs.length > 0 && msgs[msgs.length - 1].role === 'assistant') msgs.pop();
      return { ...c, messages: msgs };
    }));
    setTimeout(() => sendMessage(lastUser.content), 100);
  };

  const copyMessage = (content: string) => { navigator.clipboard.writeText(content); };
  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  return (
    <div className="h-dvh flex bg-[var(--bg-primary)] transition-colors duration-300 overflow-hidden">
      {/* ─── Overlay (mobile) ─── */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-30 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}
      {/* ─── Sidebar: drawer на мобильных, колонка на десктопе ─── */}
      <div className={`
        fixed inset-y-0 left-0 z-40 w-[85vw] max-w-xs
        md:static md:z-auto md:max-w-none
        flex flex-col bg-[var(--bg-sidebar)] border-r border-[var(--border-primary)]
        transition-all duration-300
        ${sidebarOpen
          ? 'translate-x-0 md:w-72'
          : '-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden md:border-0'}`}>
        <div className="p-3 sm:p-4 border-b border-[var(--border-primary)] flex items-center gap-2">
          <button onClick={createConversation} className="flex-1 px-4 py-3 bg-[var(--bg-button)] text-[var(--text-primary)] rounded-lg text-sm font-medium hover:bg-[var(--bg-button-hover)] transition-colors">
            <i className="fa-solid fa-plus mr-2" />Новый диалог
          </button>
          <button onClick={() => setSidebarOpen(false)}
            className="md:hidden w-11 h-11 shrink-0 rounded-lg bg-[var(--bg-button)]/40 text-[var(--text-primary)] flex items-center justify-center border border-[var(--border-primary)]">
            <i className="fa-solid fa-xmark" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto overscroll-contain p-2 space-y-1" ref={menuRef}>
          {sortedConvs.map((conv) => (
            <div key={conv.id}
              className={`group relative flex items-center gap-2 px-3 py-3 md:py-2.5 rounded-lg cursor-pointer text-sm transition-colors ${conv.id === activeId ? 'bg-[var(--bg-button)]/40 text-[var(--text-primary)]' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-button)]/20 hover:text-[var(--text-primary)]'}`}
              onClick={() => selectConversation(conv.id)}>
              {conv.pinned && <i className="fa-solid fa-thumbtack text-[10px] text-[var(--accent)] shrink-0" />}
              <i className="fa-regular fa-message text-xs shrink-0" />
              {renameId === conv.id ? (
                <input value={renameText} onChange={(e) => setRenameText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') confirmRename(); if (e.key === 'Escape') { setRenameId(null); setRenameText(''); } }}
                  onBlur={confirmRename} autoFocus
                  className="flex-1 min-w-0 bg-[var(--bg-input)] border border-[var(--border-hover)] rounded px-2 py-1 text-base md:text-xs text-[var(--text-primary)] focus:outline-none"
                  onClick={(e) => e.stopPropagation()} />
              ) : (
                <span className="truncate flex-1">{conv.title}</span>
              )}
              <button onClick={(e) => { e.stopPropagation(); setMenuId(menuId === conv.id ? null : conv.id); }}
                className="opacity-100 md:opacity-0 md:group-hover:opacity-100 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all shrink-0 px-1">
                <i className="fa-solid fa-ellipsis-vertical text-sm" />
              </button>
              {menuId === conv.id && (
                <div className="absolute right-0 top-11 w-44 bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-lg shadow-xl z-50 overflow-hidden">
                  <button onClick={(e) => { e.stopPropagation(); startRename(conv.id, conv.title); }} className="w-full px-3 py-2.5 text-left text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-button)]/30 hover:text-[var(--text-primary)] transition-colors">
                    <i className="fa-solid fa-pen mr-2 w-3" />Переименовать
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); downloadConversation(conv.id); }} className="w-full px-3 py-2.5 text-left text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-button)]/30 hover:text-[var(--text-primary)] transition-colors">
                    <i className="fa-solid fa-download mr-2 w-3" />Скачать (.md)
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); togglePin(conv.id); }} className="w-full px-3 py-2.5 text-left text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-button)]/30 hover:text-[var(--text-primary)] transition-colors">
                    <i className={`fa-solid fa-thumbtack mr-2 w-3 ${conv.pinned ? 'text-[var(--accent)]' : ''}`} />{conv.pinned ? 'Открепить' : 'Закрепить'}
                  </button>
                  <div className="border-t border-[var(--border-primary)]" />
                  <button onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }} className="w-full px-3 py-2.5 text-left text-xs text-red-400 hover:bg-red-500/10 transition-colors">
                    <i className="fa-solid fa-trash-can mr-2 w-3" />Удалить
                  </button>
                </div>
              )}
            </div>
          ))}
          {conversations.length === 0 && <p className="text-center text-[var(--text-muted)] text-xs mt-8">Нет диалогов</p>}
        </div>
        <div className="p-3 sm:p-4 border-t border-[var(--border-primary)] pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <div className="text-xs text-[var(--text-muted)] truncate mb-2" title={currentStatus}>
            <i className="fa-solid fa-circle-info mr-1" />
            {currentStatus}
          </div>
          <Link to="/" className="text-[var(--text-muted)] text-xs hover:text-[var(--text-primary)] transition-colors">
            <i className="fa-solid fa-arrow-left mr-2" />На главную
          </Link>
        </div>
      </div>
      {/* ─── Main ─── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2 sm:gap-3 px-3 sm:px-4 py-2.5 sm:py-3 border-b border-[var(--border-primary)]">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="w-10 h-10 shrink-0 flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
            <i className={`fa-solid ${sidebarOpen ? 'fa-bars-staggered' : 'fa-bars'} text-lg`} />
          </button>
          <h1 className="text-[var(--text-primary)] font-semibold text-sm truncate flex-1">{activeConv?.title || 'MAKO AI Chat'}</h1>
          {/* TTS Settings */}
          <div className="relative shrink-0" ref={ttsMenuRef}>
            <button onClick={() => setShowTtsSettings(!showTtsSettings)}
              className="w-10 h-10 rounded-lg bg-[var(--bg-button)]/50 text-[var(--text-primary)] flex items-center justify-center hover:bg-[var(--bg-button)] transition-colors border border-[var(--border-primary)]"
              title="Настройки озвучки">
              <i className="fa-solid fa-sliders text-sm" />
            </button>
            {showTtsSettings && (
              <div className="absolute right-0 top-12 w-[calc(100vw-1.5rem)] max-w-[16rem] bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl shadow-xl p-4 z-[200] space-y-4">
                <h4 className="text-[var(--text-primary)] text-xs font-bold uppercase tracking-wide">Настройки озвучки</h4>
                <div>
                  <label className="text-[var(--text-secondary)] text-xs block mb-1">Голос</label>
                  <select value={ttsSettings.voice} onChange={(e) => setTtsSettings((p) => ({ ...p, voice: e.target.value }))}
                    className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-hover)]">
                    {TTS_VOICES.map((v) => <option key={v.id} value={v.id}>{v.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[var(--text-secondary)] text-xs block mb-1">Скорость: {ttsSettings.speed.toFixed(1)}x</label>
                  <input type="range" min="0.5" max="2.0" step="0.1" value={ttsSettings.speed}
                    onChange={(e) => setTtsSettings((p) => ({ ...p, speed: parseFloat(e.target.value) }))}
                    className="w-full accent-[var(--accent)]" />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-[var(--text-secondary)] text-xs">Автоозвучка ответов</label>
                  <button onClick={() => setTtsSettings((p) => ({ ...p, autoPlay: !p.autoPlay }))}
                    className={`w-10 h-5 rounded-full transition-colors relative shrink-0 ${ttsSettings.autoPlay ? 'bg-[var(--accent)]' : 'bg-[var(--border-primary)]'}`}>
                    <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${ttsSettings.autoPlay ? 'left-[22px]' : 'left-0.5'}`} />
                  </button>
                </div>
              </div>
            )}
          </div>
          <ThemeSwitcher />
        </div>
        {/* Messages */}
        <div className="flex-1 overflow-y-auto overscroll-contain px-3 sm:px-4 py-4 sm:py-6">
          {!activeConv || activeConv.messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <i className="fa-solid fa-robot text-5xl text-[var(--text-muted)] mb-4" />
              <p className="text-[var(--text-secondary)] text-sm">Начните диалог с MAKO AI</p>
              <p className="text-[var(--text-muted)] text-xs mt-1">Orchestrator направит запрос нужному агенту</p>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-3 sm:space-y-4">
              {activeConv.messages.map((msg) => (
                <div key={msg.id} className={`group flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[92%] sm:max-w-[85%] rounded-xl px-3.5 sm:px-4 py-2.5 sm:py-3 text-sm relative ${msg.role === 'user' ? 'bg-[var(--bg-message-user)] text-[var(--text-primary)] rounded-br-sm' : 'bg-[var(--bg-message-assistant)] border border-[var(--border-primary)] text-[var(--text-primary)] rounded-bl-sm'}`}>
                    {msg.role === 'assistant' ? (
                      msg.content ? <MarkdownContent content={msg.content} /> : (
                        <span className="inline-flex items-center gap-1 text-[var(--text-muted)]">
                          <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <span className="w-1.5 h-1.5 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </span>
                      )
                    ) : <p className="whitespace-pre-wrap">{msg.content}</p>}
                    {msg.role === 'assistant' && msg.content && (
                      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 pt-2 border-t border-[var(--border-primary)] opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                        <button onClick={() => playTTS(msg.content, msg.id)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs transition-colors">
                          <i className={`fa-solid ${playingId === msg.id ? 'fa-stop' : 'fa-volume-high'} mr-1`} />{playingId === msg.id ? 'Стоп' : 'Озвучить'}
                        </button>
                        <button onClick={() => copyMessage(msg.content)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs transition-colors">
                          <i className="fa-regular fa-copy mr-1" />Копировать
                        </button>
                        <button onClick={retryLast} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs transition-colors">
                          <i className="fa-solid fa-rotate-right mr-1" />Повторить
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
        {/* Input */}
        <div className="px-3 sm:px-4 py-3 sm:py-4 border-t border-[var(--border-primary)] pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <div className="max-w-3xl mx-auto flex gap-2 sm:gap-3 items-end">
            <button onClick={toggleVoice}
              className={`w-12 h-12 shrink-0 rounded-xl transition-all flex items-center justify-center ${listening ? 'bg-red-500/80 text-white animate-pulse' : 'bg-[var(--bg-button)]/50 text-[var(--text-primary)] hover:bg-[var(--bg-button)] border border-[var(--border-primary)]'}`}
              title={listening ? 'Остановить запись' : 'Голосовой ввод'}>
              <i className={`fa-solid ${listening ? 'fa-stop' : 'fa-microphone'}`} />
            </button>
            <textarea ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder={listening ? 'Запись... Говорите' : 'Введите сообщение...'}
              rows={1}
              className="flex-1 min-w-0 resize-none bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-3.5 sm:px-4 py-3 text-base sm:text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-hover)] transition-colors max-h-32"
              style={{ minHeight: '48px' }} />
            <button onClick={() => sendMessage()} disabled={streaming || !input.trim()}
              className="w-12 h-12 shrink-0 bg-[var(--bg-button)] text-[var(--text-primary)] rounded-xl hover:bg-[var(--bg-button-hover)] disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center">
              <i className={`fa-solid ${streaming ? 'fa-spinner fa-spin' : 'fa-paper-plane'}`} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;