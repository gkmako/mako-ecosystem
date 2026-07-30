import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import mermaid from 'mermaid';

type Theme = 'default' | 'dark' | 'forest' | 'neutral';
type Direction = 'TB' | 'BT' | 'LR' | 'RL';
type Curve = 'basis' | 'linear' | 'step' | 'cardinal';
type Layout = 'dagre' | 'elk';

interface DiagramConfig {
  theme: Theme;
  direction: Direction;
  curve: Curve;
  layout: Layout;
}

const DEFAULT_CODE = `graph TD
  A[Start] --> B{Decision}
  B -->|Yes| C[OK]
  B -->|No| D[Cancel]
  C --> E[End]
  D --> E`;

// localStorage keys
const STORAGE_KEY_CODE = 'makotools_diagram_code';
const STORAGE_KEY_CONFIG = 'makotools_diagram_config';
const STORAGE_KEY_VIEW = 'makotools_diagram_view';

const DEFAULT_CONFIG: DiagramConfig = {
  theme: 'default',
  direction: 'TB',
  curve: 'basis',
  layout: 'dagre',
};

const DEFAULT_VIEW = { zoom: 1, panX: 0, panY: 0 };

const injectMermaidInit = (code: string, config: DiagramConfig): string => {
  let cleaned = code.trim();

  const yamlMatch = cleaned.match(/^config:\s*\n[\s\S]*?\n---\s*\n/);
  if (yamlMatch) {
    cleaned = cleaned.slice(yamlMatch[0].length).trim();
  }
  cleaned = cleaned.replace(/%%\{init:\s*[^%]*\}%%\s*/g, '').trim();

  const diagramTypeMatch = cleaned.match(
    /^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram-v2|erDiagram|gantt|pie|gitgraph|mindmap|timeline|journey|C4Context|quadrantChart|xychart-beta)\s*(\w+)?/m
  );
  if (diagramTypeMatch) {
    const type = diagramTypeMatch[1];
    const isFlowchart = type === 'graph' || type === 'flowchart';
    if (isFlowchart) {
      const currentDir = diagramTypeMatch[2];
      const validDirs = ['TB', 'BT', 'LR', 'RL', 'TD'];
      if (validDirs.includes(currentDir || '')) {
        cleaned = cleaned.replace(
          new RegExp(`^(${type})\\s+\\w+`, 'm'),
          `$1 ${config.direction}`
        );
      } else if (!currentDir) {
        cleaned = cleaned.replace(
          new RegExp(`^(${type})\\b`, 'm'),
          `$1 ${config.direction}`
        );
      }
    }
  }

  const initConfig: Record<string, any> = {
    theme: config.theme,
    flowchart: {
      curve: config.curve,
      htmlLabels: true,
      useMaxWidth: false,
    },
    securityLevel: 'loose',
  };
  if (config.layout === 'elk') {
    initConfig.flowchart.defaultRenderer = 'elk';
  }
  return `%%{init: ${JSON.stringify(initConfig)}}%%\n${cleaned}`;
};

const DiagramStudio: React.FC = () => {
  const [code, setCode] = useState<string>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_CODE);
    return saved !== null ? saved : DEFAULT_CODE;
  });
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<DiagramConfig>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_CONFIG);
    if (saved) {
      try {
        return { ...DEFAULT_CONFIG, ...JSON.parse(saved) };
      } catch {
        return DEFAULT_CONFIG;
      }
    }
    return DEFAULT_CONFIG;
  });
  const [isRendering, setIsRendering] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Zoom & Pan
  const [zoom, setZoom] = useState<number>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_VIEW);
    if (saved) {
      try {
        const view = JSON.parse(saved);
        return typeof view.zoom === 'number' ? view.zoom : DEFAULT_VIEW.zoom;
      } catch {
        return DEFAULT_VIEW.zoom;
      }
    }
    return DEFAULT_VIEW.zoom;
  });
  const [pan, setPan] = useState<{ x: number; y: number }>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_VIEW);
    if (saved) {
      try {
        const view = JSON.parse(saved);
        return {
          x: typeof view.panX === 'number' ? view.panX : DEFAULT_VIEW.panX,
          y: typeof view.panY === 'number' ? view.panY : DEFAULT_VIEW.panY,
        };
      } catch {
        return { x: DEFAULT_VIEW.panX, y: DEFAULT_VIEW.panY };
      }
    }
    return { x: DEFAULT_VIEW.panX, y: DEFAULT_VIEW.panY };
  });

  const [isDragging, setIsDragging] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);

  const dragStartRef = useRef({ x: 0, y: 0 });
  const panStartRef = useRef({ x: 0, y: 0 });
  const diagramRef = useRef<HTMLDivElement>(null);
  const previewContainerRef = useRef<HTMLDivElement>(null);
  const idCounter = useRef(0);

  // === Автосохранение в localStorage ===
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CODE, code);
    } catch (e) {
      console.warn('Failed to save code to localStorage:', e);
    }
  }, [code]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CONFIG, JSON.stringify(config));
    } catch (e) {
      console.warn('Failed to save config to localStorage:', e);
    }
  }, [config]);

  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY_VIEW,
        JSON.stringify({ zoom, panX: pan.x, panY: pan.y })
      );
    } catch (e) {
      console.warn('Failed to save view to localStorage:', e);
    }
  }, [zoom, pan]);

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
  }, []);

  const renderDiagram = useCallback(async () => {
    if (!diagramRef.current) return;
    setIsRendering(true);
    setError(null);
    try {
      const codeWithInit = injectMermaidInit(code, config);
      if (config.layout === 'elk') {
        const response = await fetch('/api/mermaid/render-elk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: codeWithInit, config }),
        });
        if (!response.ok) {
          const err = await response.text();
          throw new Error(`ELK render failed (${response.status}): ${err}`);
        }
        const svgText = await response.text();
        if (!svgText.includes('<svg')) {
          throw new Error(`Invalid SVG: ${svgText.slice(0, 200)}`);
        }
        diagramRef.current.innerHTML = svgText;
      } else {
        idCounter.current += 1;
        const id = `mermaid-${idCounter.current}`;
        diagramRef.current.innerHTML = '';
        const { svg } = await mermaid.render(id, codeWithInit);
        diagramRef.current.innerHTML = svg;
      }
    } catch (e: any) {
      setError(e?.message || 'Ошибка рендеринга');
      if (diagramRef.current) diagramRef.current.innerHTML = '';
    } finally {
      setIsRendering(false);
    }
  }, [code, config]);

  useEffect(() => {
    const timer = setTimeout(renderDiagram, 400);
    return () => clearTimeout(timer);
  }, [renderDiagram]);

  // Space → hand mode
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        const t = e.target as HTMLElement;
        if (t?.tagName === 'TEXTAREA' || t?.tagName === 'INPUT' || t?.isContentEditable) return;
        if (!isSpacePressed) {
          e.preventDefault();
          setIsSpacePressed(true);
        }
      }
    };
    const up = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
        setIsDragging(false);
      }
    };
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
    };
  }, [isSpacePressed]);

  // Ctrl + Wheel → Zoom
  useEffect(() => {
    const el = previewContainerRef.current;
    if (!el) return;
    const handler = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      const d = e.deltaY > 0 ? 0.9 : 1.1;
      setZoom((p) => Math.max(0.1, Math.min(5, p * d)));
    };
    el.addEventListener('wheel', handler, { passive: false });
    return () => el.removeEventListener('wheel', handler);
  }, []);

  const onMouseDown = (e: React.MouseEvent) => {
    if (!isSpacePressed || e.button !== 0) return;
    e.preventDefault();
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    panStartRef.current = { ...pan };
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !isSpacePressed) return;
    setPan({
      x: panStartRef.current.x + (e.clientX - dragStartRef.current.x),
      y: panStartRef.current.y + (e.clientY - dragStartRef.current.y),
    });
  };
  const onMouseUp = () => setIsDragging(false);

  const resetView = () => {
    setZoom(DEFAULT_VIEW.zoom);
    setPan({ x: DEFAULT_VIEW.panX, y: DEFAULT_VIEW.panY });
  };

  // Modal state
  const [showPdfModal, setShowPdfModal] = useState(false);
  const [pdfFormat, setPdfFormat] = useState<'A0' | 'A1' | 'A2' | 'A3' | 'A4' | 'A5' | 'A6' | 'Custom'>('A4');
  const [pdfOrientation, setPdfOrientation] = useState<'Portrait' | 'Landscape'>('Portrait');
  const [pdfMargin, setPdfMargin] = useState(10);
  const [pdfFitMode, setPdfFitMode] = useState<'fit_to_page' | 'actual_size_with_pagination'>('fit_to_page');

  const exportPDF = async () => {
    if (error || isRendering) return;
    setIsExporting(true);
    try {
      const codeWithInit = injectMermaidInit(code, config);
      const response = await fetch('/api/mermaid/render-pdf-advanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: codeWithInit,
          config,
          pdf_options: {
            format: pdfFormat,
            orientation: pdfOrientation,
            margin_mm: pdfMargin,
            fit_mode: pdfFitMode,
          },
        }),
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`PDF failed (${response.status}): ${errorText}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'diagram.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Ошибка PDF: ' + (e as Error).message);
    } finally {
      setIsExporting(false);
    }
  };

  const exportSVG = () => {
    if (!diagramRef.current || error) return;
    const svg = diagramRef.current.querySelector('svg');
    if (!svg) return;
    const clone = svg.cloneNode(true) as SVGSVGElement;
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const blob = new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'diagram.svg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const cursor = !isSpacePressed ? 'default' : isDragging ? 'grabbing' : 'grab';

  return (
    <div className="h-screen bg-[var(--bg-primary)] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-primary)] shrink-0">
        <Link to="/" className="flex items-center gap-2 text-[var(--text-primary)] hover:text-[var(--text-accent)]">
          <i className="fa-solid fa-arrow-left" />
          <span className="font-semibold hidden sm:inline">На главную</span>
        </Link>
        <h1 className="text-lg font-bold text-[var(--text-primary)]">
          <i className="fa-solid fa-diagram-project mr-2" />Diagram Studio
        </h1>
        <div className="w-24" />
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 px-4 py-2 bg-[var(--bg-card)] border-b border-[var(--border-primary)] shrink-0">
        {([
          ['Theme', 'theme', ['default', 'dark', 'forest', 'neutral']],
          ['Direction', 'direction', ['TB', 'BT', 'LR', 'RL']],
          ['Curve', 'curve', ['basis', 'linear', 'step', 'cardinal']],
          ['Layout', 'layout', ['dagre', 'elk']],
        ] as const).map(([label, key, options]) => (
          <div key={key} className="flex flex-col gap-0.5">
            <label className="text-[10px] text-[var(--text-muted)] uppercase">{label}</label>
            <select
              value={config[key]}
              onChange={(e) => setConfig({ ...config, [key]: e.target.value as any })}
              className="px-2 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-xs text-[var(--text-primary)]"
            >
              {options.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </div>
        ))}
      </div>

      {/* MAIN: код СЛЕВА (25%), gap, превью СПРАВА (75%) */}
      <div
        className="flex-1 min-h-0 p-4 gap-4"
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(280px, 25fr) 75fr',
        }}
      >
        {/* ── CODE (left, 25%) ── */}
        <div className="flex flex-col min-w-0 overflow-hidden">
          <label className="text-xs font-semibold text-[var(--text-primary)] mb-2 uppercase tracking-wide shrink-0 flex items-center gap-2">
            <i className="fa-solid fa-code" />Mermaid код
          </label>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="flex-1 min-h-0 p-3 bg-[var(--bg-card)] text-[var(--text-primary)] border border-[var(--border-primary)] rounded-xl font-mono text-xs resize-none focus:outline-none focus:border-[var(--border-hover)]"
            spellCheck={false}
          />
        </div>

        {/* ── PREVIEW (right, 75%) ── */}
        <div className="flex flex-col min-w-0 overflow-hidden">
          <div className="flex items-center justify-between mb-2 shrink-0">
            <label className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wide flex items-center gap-2">
              <i className="fa-solid fa-eye" />Превью
              {isSpacePressed && (
                <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-500 rounded text-[10px] normal-case font-normal">
                  <i className="fa-solid fa-hand mr-1" />Рука
                </span>
              )}
            </label>
            <div className="flex items-center gap-1">
              <button onClick={() => setZoom(z => Math.min(5, z * 1.2))} className="w-6 h-6 bg-[var(--bg-button)] border border-[var(--border-primary)] rounded text-[10px] text-[var(--text-primary)] flex items-center justify-center"><i className="fa-solid fa-plus" /></button>
              <button onClick={() => setZoom(z => Math.max(0.1, z * 0.8))} className="w-6 h-6 bg-[var(--bg-button)] border border-[var(--border-primary)] rounded text-[10px] text-[var(--text-primary)] flex items-center justify-center"><i className="fa-solid fa-minus" /></button>
              <button onClick={resetView} className="w-6 h-6 bg-[var(--bg-button)] border border-[var(--border-primary)] rounded text-[10px] text-[var(--text-primary)] flex items-center justify-center"><i className="fa-solid fa-expand" /></button>
              <span className="ml-1 text-[10px] text-[var(--text-muted)] w-8 text-right">{Math.round(zoom * 100)}%</span>
            </div>
          </div>
          <div
            ref={previewContainerRef}
            className="flex-1 min-h-0 relative bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl overflow-auto"
            style={{ cursor }}
            onMouseDown={onMouseDown}
            onMouseMove={onMouseMove}
            onMouseUp={onMouseUp}
            onMouseLeave={onMouseUp}
          >
            {isRendering && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/20 z-20">
                <i className="fa-solid fa-spinner fa-spin text-2xl text-white" />
              </div>
            )}
            {error ? (
              <div className="absolute inset-0 flex items-center justify-center p-4 overflow-auto">
                <div className="text-red-500 text-sm max-w-md">
                  <i className="fa-solid fa-triangle-exclamation text-xl mb-2 block" />
                  <div className="font-mono text-xs whitespace-pre-wrap break-words">{error}</div>
                </div>
              </div>
            ) : (
              <div className="w-full h-full">
                <div
                  ref={diagramRef}
                  className="inline-block p-8"
                  style={{
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                    transformOrigin: 'top left',
                    transition: isDragging ? 'none' : 'transform 0.1s ease-out',
                    minWidth: '100%',
                    minHeight: '100%',
                  }}
                />
              </div>
            )}
            {!error && !isRendering && (
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] text-[var(--text-muted)] bg-[var(--bg-primary)]/80 px-3 py-1 rounded-full pointer-events-none whitespace-nowrap">
                <kbd className="px-1 bg-[var(--bg-card)] rounded">Ctrl</kbd>+<i className="fa-solid fa-computer-mouse mx-1" />=Zoom
                <span className="mx-2">•</span>
                <kbd className="px-1 bg-[var(--bg-card)] rounded">Space</kbd>+drag=Pan
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex flex-wrap gap-3 px-4 py-3 border-t border-[var(--border-primary)] shrink-0">
        <button
          onClick={() => setShowPdfModal(true)}
          disabled={!!error || isRendering || isExporting}
          className="px-6 py-2 bg-[var(--bg-button)] text-[var(--text-primary)] rounded-xl text-sm font-semibold hover:bg-[var(--bg-button-hover)] transition-all border border-[var(--border-hover)] disabled:opacity-50"
        >
          <i className={`fa-solid ${isExporting ? 'fa-spinner fa-spin' : 'fa-file-pdf'} mr-2`} />
          PDF (вектор)
        </button>
        <button
          onClick={exportSVG}
          disabled={!!error || isRendering}
          className="px-6 py-2 bg-[var(--bg-button)]/70 text-[var(--text-primary)] rounded-xl text-sm font-semibold hover:bg-[var(--bg-button)] transition-all border border-[var(--border-primary)] disabled:opacity-50"
        >
          <i className="fa-solid fa-file-code mr-2" />SVG
        </button>
        <button onClick={resetView} className="px-6 py-2 bg-[var(--bg-button)]/50 text-[var(--text-primary)] rounded-xl text-sm font-semibold hover:bg-[var(--bg-button)] transition-all border border-[var(--border-primary)]">
          <i className="fa-solid fa-expand mr-2" />Сбросить вид
        </button>
        <button
          onClick={() => {
            setCode(DEFAULT_CODE);
            resetView();
          }}
          className="px-6 py-2 bg-[var(--bg-button)]/50 text-[var(--text-primary)] rounded-xl text-sm font-semibold hover:bg-[var(--bg-button)] transition-all border border-[var(--border-primary)]"
        >
          <i className="fa-solid fa-rotate-right mr-2" />Сбросить код
        </button>
      </div>

      {/* PDF Export Modal */}
      {showPdfModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Параметры PDF</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Формат листа</label>
                <select
                  value={pdfFormat}
                  onChange={(e) => setPdfFormat(e.target.value as any)}
                  className="w-full p-2 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)]"
                >
                  <option value="A0">A0 (841×1189мм)</option>
                  <option value="A1">A1 (594×841мм)</option>
                  <option value="A2">A2 (420×594мм)</option>
                  <option value="A3">A3 (297×420мм)</option>
                  <option value="A4">A4 (210×297мм)</option>
                  <option value="A5">A5 (148×210мм)</option>
                  <option value="A6">A6 (105×148мм)</option>
                  <option value="Custom">Custom (A1)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Ориентация</label>
                <select
                  value={pdfOrientation}
                  onChange={(e) => setPdfOrientation(e.target.value as any)}
                  className="w-full p-2 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)]"
                >
                  <option value="Portrait">Книжная</option>
                  <option value="Landscape">Альбомная</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Поля (мм)</label>
                <input
                  type="number"
                  value={pdfMargin}
                  onChange={(e) => setPdfMargin(Number(e.target.value))}
                  min="0"
                  max="50"
                  step="1"
                  className="w-full p-2 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)]"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Масштабирование</label>
                <select
                  value={pdfFitMode}
                  onChange={(e) => setPdfFitMode(e.target.value as any)}
                  className="w-full p-2 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)]"
                >
                  <option value="fit_to_page">Вписать в страницу</option>
                  <option value="actual_size_with_pagination">Фактический размер (с продолжением)</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowPdfModal(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Отмена
              </button>
              <button
                onClick={exportPDF}
                disabled={isExporting}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {isExporting ? 'Экспорт...' : 'Экспортировать'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiagramStudio;