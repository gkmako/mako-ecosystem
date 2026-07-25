import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import mermaid from 'mermaid';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

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

const DiagramStudio: React.FC = () => {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<DiagramConfig>({
    theme: 'default',
    direction: 'TB',
    curve: 'basis',
    layout: 'dagre',
  });
  const [isRendering, setIsRendering] = useState(false);

  // Zoom & Pan state
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const panStartRef = useRef({ x: 0, y: 0 });

  const diagramRef = useRef<HTMLDivElement>(null);
  const previewContainerRef = useRef<HTMLDivElement>(null);
  const idCounter = useRef(0);

  // Initialize mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: config.theme,
      securityLevel: 'loose',
      flowchart: {
        curve: config.curve,
        htmlLabels: true,
        useMaxWidth: false,
      },
    });
  }, [config.theme, config.curve]);

  // Render diagram
  const renderDiagram = useCallback(async () => {
    if (!diagramRef.current) return;

    setIsRendering(true);
    try {
      let codeToRender = code;

      if (config.layout === 'elk') {
        const response = await fetch('/api/mermaid/render-elk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, config }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText);
        }
        const svgText = await response.text();
        diagramRef.current.innerHTML = svgText;
      } else {
        idCounter.current += 1;
        const id = `mermaid-${idCounter.current}`;

        if (config.direction !== 'TB') {
          codeToRender = codeToRender.replace(/^(graph|flowchart)\s+\w+/m, `$1 ${config.direction}`);
        }

        const { svg } = await mermaid.render(id, codeToRender);
        diagramRef.current.innerHTML = svg;
      }

      setError(null);
    } catch (e: any) {
      setError(e?.message || 'Ошибка синтаксиса Mermaid');
      diagramRef.current.innerHTML = '';
    } finally {
      setIsRendering(false);
    }
  }, [code, config]);

  useEffect(() => {
    const timer = setTimeout(renderDiagram, 400);
    return () => clearTimeout(timer);
  }, [renderDiagram]);

  // Space key for "hand" mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !isSpacePressed) {
        // Не перехватываем Space если фокус в textarea
        if ((e.target as HTMLElement)?.tagName === 'TEXTAREA') return;
        e.preventDefault();
        setIsSpacePressed(true);
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
        setIsDragging(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isSpacePressed]);

  // Wheel zoom (passive: false для preventDefault)
  useEffect(() => {
    const container = previewContainerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      if (!isSpacePressed) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        setZoom((prev) => Math.max(0.1, Math.min(5, prev * delta)));
      }
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [isSpacePressed]);

  // Mouse drag handlers for pan
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!isSpacePressed || e.button !== 0) return;
    e.preventDefault();
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    panStartRef.current = { ...pan };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !isSpacePressed) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    setPan({
      x: panStartRef.current.x + dx,
      y: panStartRef.current.y + dy,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Reset view
  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // PDF export (через html2canvas — можно заменить на svg2pdf.js позже)
  const exportPDF = async () => {
    if (!diagramRef.current || error) return;
    try {
      const canvas = await html2canvas(diagramRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
        unit: 'mm',
        format: 'a4',
      });
      const pageW = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();
      const ratio = Math.min(pageW / canvas.width, pageH / canvas.height);
      const w = canvas.width * ratio;
      const h = canvas.height * ratio;
      pdf.addImage(imgData, 'PNG', (pageW - w) / 2, (pageH - h) / 2, w, h);
      pdf.save('diagram.pdf');
    } catch (e) {
      console.error('PDF export error:', e);
    }
  };

  // Курсор в зависимости от режима
  const getCursor = () => {
    if (!isSpacePressed) return 'default';
    return isDragging ? 'grabbing' : 'grab';
  };

  return (
    <div className="h-screen bg-[var(--bg-primary)] flex flex-col transition-colors duration-300 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-3 border-b border-[var(--border-primary)] flex-shrink-0">
        <Link
          to="/"
          className="flex items-center gap-2 text-[var(--text-primary)] hover:text-[var(--text-accent)] transition-colors"
        >
          <i className="fa-solid fa-arrow-left" />
          <span className="font-semibold hidden sm:inline">На главную</span>
        </Link>
        <h1 className="text-lg sm:text-xl font-bold text-[var(--text-primary)]">
          <i className="fa-solid fa-diagram-project mr-2" />
          Diagram Studio
        </h1>
        <div className="w-24" />
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 px-4 sm:px-6 py-3 bg-[var(--bg-card)] border-b border-[var(--border-primary)] flex-shrink-0">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-[var(--text-muted)]">Theme</label>
          <select
            value={config.theme}
            onChange={(e) => setConfig({ ...config, theme: e.target.value as Theme })}
            className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-sm text-[var(--text-primary)]"
          >
            <option value="default">Default</option>
            <option value="dark">Dark</option>
            <option value="forest">Forest</option>
            <option value="neutral">Neutral</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-[var(--text-muted)]">Direction</label>
          <select
            value={config.direction}
            onChange={(e) => setConfig({ ...config, direction: e.target.value as Direction })}
            className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-sm text-[var(--text-primary)]"
          >
            <option value="TB">Top → Bottom</option>
            <option value="BT">Bottom → Top</option>
            <option value="LR">Left → Right</option>
            <option value="RL">Right → Left</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-[var(--text-muted)]">Curve</label>
          <select
            value={config.curve}
            onChange={(e) => setConfig({ ...config, curve: e.target.value as Curve })}
            className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-sm text-[var(--text-primary)]"
          >
            <option value="basis">Basis</option>
            <option value="linear">Linear</option>
            <option value="step">Step</option>
            <option value="cardinal">Cardinal</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-[var(--text-muted)]">Layout</label>
          <select
            value={config.layout}
            onChange={(e) => setConfig({ ...config, layout: e.target.value as Layout })}
            className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-sm text-[var(--text-primary)]"
          >
            <option value="dagre">Dagre (default)</option>
            <option value="elk">ELK (advanced)</option>
          </select>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col px-4 sm:px-6 pt-4 pb-2 min-h-0 overflow-hidden">
        {/* Code block: 30vh */}
        <div style={{ height: '30vh' }} className="flex flex-col flex-shrink-0">
          <label className="text-xs sm:text-sm font-semibold text-[var(--text-primary)] mb-2 uppercase tracking-wide flex items-center gap-2">
            <i className="fa-solid fa-code" />
            Mermaid код
          </label>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="flex-1 p-4 bg-[var(--bg-card)] text-[var(--text-primary)] border border-[var(--border-primary)] rounded-xl font-mono text-xs sm:text-sm resize-none focus:outline-none focus:border-[var(--border-hover)] transition-colors overflow-auto"
            spellCheck={false}
          />
        </div>

        {/* Spacing: 3vh */}
        <div style={{ height: '3vh' }} className="flex-shrink-0" />

        {/* Preview: fills remaining space */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs sm:text-sm font-semibold text-[var(--text-primary)] uppercase tracking-wide flex items-center gap-2">
              <i className="fa-solid fa-eye" />
              Превью
              {isSpacePressed && (
                <span className="ml-2 px-2 py-0.5 bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 rounded text-xs font-normal normal-case">
                  <i className="fa-solid fa-hand mr-1" />
                  Режим «Рука» — зажмите и тяните
                </span>
              )}
            </label>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setZoom((z) => Math.min(5, z * 1.2))}
                className="w-7 h-7 bg-[var(--bg-button)] border border-[var(--border-primary)] rounded hover:bg-[var(--bg-button-hover)] flex items-center justify-center text-xs"
                title="Увеличить"
              >
                <i className="fa-solid fa-plus" />
              </button>
              <button
                onClick={() => setZoom((z) => Math.max(0.1, z * 0.8))}
                className="w-7 h-7 bg-[var(--bg-button)] border border-[var(--border-primary)] rounded hover:bg-[var(--bg-button-hover)] flex items-center justify-center text-xs"
                title="Уменьшить"
              >
                <i className="fa-solid fa-minus" />
              </button>
              <button
                onClick={resetView}
                className="w-7 h-7 bg-[var(--bg-button)] border border-[var(--border-primary)] rounded hover:bg-[var(--bg-button-hover)] flex items-center justify-center text-xs"
                title="Сбросить вид"
              >
                <i className="fa-solid fa-expand" />
              </button>
              <span className="ml-2 text-xs text-[var(--text-muted)] min-w-[3rem] text-right">
                {Math.round(zoom * 100)}%
              </span>
            </div>
          </div>

          {/* Preview container */}
          <div
            ref={previewContainerRef}
            className="flex-1 relative bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl overflow-hidden"
            style={{ cursor: getCursor() }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* Loading */}
            {isRendering && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/20 z-20">
                <i className="fa-solid fa-spinner fa-spin text-2xl text-white" />
              </div>
            )}

            {/* Error */}
            {error ? (
              <div className="absolute inset-0 flex items-center justify-center p-4">
                <div className="text-red-500 text-sm text-center max-w-md">
                  <i className="fa-solid fa-triangle-exclamation text-2xl mb-2 block" />
                  {error}
                </div>
              </div>
            ) : (
              /* Scrollable area with transform */
              <div className="w-full h-full overflow-auto">
                <div
                  ref={diagramRef}
                  className="inline-block p-8 min-w-full min-h-full"
                  style={{
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                    transformOrigin: 'top left',
                    transition: isDragging ? 'none' : 'transform 0.1s ease-out',
                  }}
                />
              </div>
            )}

            {/* Hint at bottom */}
            {!error && !isRendering && (
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-[var(--text-muted)] bg-[var(--bg-primary)]/80 px-3 py-1 rounded-full pointer-events-none">
                <i className="fa-solid fa-mouse-pointer mr-1" />
                Колесо = Zoom • <kbd className="px-1 bg-[var(--bg-card)] rounded text-[10px]">Space</kbd> + drag = Pan
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Actions footer */}
      <div className="flex flex-wrap gap-3 px-4 sm:px-6 py-3 border-t border-[var(--border-primary)] flex-shrink-0">
        <button
          onClick={exportPDF}
          disabled={!!error || isRendering}
          className="px-5 sm:px-8 py-2 sm:py-3 bg-[var(--bg-button)] text-[var(--text-primary)] rounded-xl text-sm sm:text-base font-semibold hover:bg-[var(--bg-button-hover)] hover:scale-105 transition-all shadow-lg border border-[var(--border-hover)] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          <i className="fa-solid fa-file-pdf mr-2" />
          Экспорт в PDF
        </button>
        <button
          onClick={resetView}
          className="px-5 sm:px-8 py-2 sm:py-3 bg-[var(--bg-button)]/50 text-[var(--text-primary)] rounded-xl text-sm sm:text-base font-semibold hover:bg-[var(--bg-button)] transition-all border border-[var(--border-primary)]"
        >
          <i className="fa-solid fa-expand mr-2" />
          Сбросить вид
        </button>
        <button
          onClick={() => setCode(DEFAULT_CODE)}
          className="px-5 sm:px-8 py-2 sm:py-3 bg-[var(--bg-button)]/50 text-[var(--text-primary)] rounded-xl text-sm sm:text-base font-semibold hover:bg-[var(--bg-button)] transition-all border border-[var(--border-primary)]"
        >
          <i className="fa-solid fa-rotate-right mr-2" />
          Сбросить код
        </button>
      </div>
    </div>
  );
};

export default DiagramStudio;