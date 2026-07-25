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
  const diagramRef = useRef<HTMLDivElement>(null);
  const idCounter = useRef(0);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: config.theme,
      securityLevel: 'loose',
      flowchart: {
        curve: config.curve,
        htmlLabels: true,
        useMaxWidth: true,
      },
    });
  }, [config.theme, config.curve]);

  const renderDiagram = useCallback(async () => {
    if (!diagramRef.current) return;
    
    setIsRendering(true);
    try {
      let codeToRender = code;
      
      // Если выбран ELK, отправляем на бэкенд
      if (config.layout === 'elk') {
        const response = await fetch('/api/render-mermaid', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, config }),
        });
        
        if (!response.ok) throw new Error('ELK rendering failed');
        const svgText = await response.text();
        diagramRef.current.innerHTML = svgText;
      } else {
        // Стандартный рендеринг через mermaid
        idCounter.current += 1;
        const id = `mermaid-${idCounter.current}`;
        
        // Добавляем direction в код если нужно
        if (config.direction !== 'TB') {
          codeToRender = code.replace(/^(graph|flowchart)\s+\w+/m, `$1 ${config.direction}`);
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

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col transition-colors duration-300">
      {/* Header */}
      <div className="flex items-center justify-between p-4 sm:p-6 border-b border-[var(--border-primary)]">
        <Link
          to="/"
          className="flex items-center gap-2 text-[var(--text-primary)] hover:text-[var(--text-accent)] transition-colors"
        >
          <i className="fa-solid fa-arrow-left" />
          <span className="font-semibold">На главную</span>
        </Link>
        <h1 className="text-lg sm:text-xl font-bold text-[var(--text-primary)]">
          <i className="fa-solid fa-diagram-project mr-2" />
          Diagram Studio
        </h1>
        <div className="w-24" />
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 p-4 bg-[var(--bg-card)] border-b border-[var(--border-primary)]">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-[var(--text-muted)]">Theme</label>
          <select
            value={config.theme}
            onChange={(e) => setConfig({ ...config, theme: e.target.value as Theme })}
            className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-sm"
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
            className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-sm"
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
            className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-sm"
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
            className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-sm"
          >
            <option value="dagre">Dagre (default)</option>
            <option value="elk">ELK (advanced)</option>
          </select>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 sm:p-6 min-h-0">
        {/* Editor */}
        <div className="flex-1 flex flex-col min-h-[300px] lg:min-h-0">
          <label className="text-xs sm:text-sm font-semibold text-[var(--text-primary)] mb-2 uppercase tracking-wide">
            <i className="fa-solid fa-code mr-2" />
            Mermaid код
          </label>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="flex-1 p-4 bg-[var(--bg-card)] text-[var(--text-primary)] border border-[var(--border-primary)] rounded-xl font-mono text-xs sm:text-sm resize-none focus:outline-none focus:border-[var(--border-hover)] transition-colors"
            spellCheck={false}
          />
        </div>

        {/* Preview */}
        <div className="flex-1 flex flex-col min-h-[300px] lg:min-h-0">
          <label className="text-xs sm:text-sm font-semibold text-[var(--text-primary)] mb-2 uppercase tracking-wide">
            <i className="fa-solid fa-eye mr-2" />
            Превью
          </label>
          <div className="flex-1 p-4 bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl overflow-auto flex items-center justify-center relative">
            {isRendering && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/20 rounded-xl">
                <i className="fa-solid fa-spinner fa-spin text-2xl text-white" />
              </div>
            )}
            {error ? (
              <div className="text-red-500 text-sm text-center p-4">
                <i className="fa-solid fa-triangle-exclamation text-2xl mb-2 block" />
                {error}
              </div>
            ) : (
              <div ref={diagramRef} className="flex items-center justify-center" />
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3 p-4 sm:p-6 border-t border-[var(--border-primary)]">
        <button
          onClick={exportPDF}
          disabled={!!error || isRendering}
          className="px-5 sm:px-8 py-3 sm:py-4 bg-[var(--bg-button)] text-[var(--text-primary)] rounded-xl text-sm sm:text-base font-semibold hover:bg-[var(--bg-button-hover)] hover:scale-105 transition-all shadow-lg border border-[var(--border-hover)] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          <i className="fa-solid fa-file-pdf mr-2" />
          Экспорт в PDF
        </button>
        <button
          onClick={() => setCode(DEFAULT_CODE)}
          className="px-5 sm:px-8 py-3 sm:py-4 bg-[var(--bg-button)]/50 text-[var(--text-primary)] rounded-xl text-sm sm:text-base font-semibold hover:bg-[var(--bg-button)] transition-all border border-[var(--border-primary)]"
        >
          <i className="fa-solid fa-rotate-right mr-2" />
          Сброс
        </button>
      </div>
    </div>
  );
};

export default DiagramStudio;