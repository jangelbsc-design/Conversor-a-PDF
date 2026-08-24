"use client";

import React, { useEffect, useState } from "react";
import { api } from "../lib/api";

interface PagePreviewProps {
  docId: string;
  onPageClick?: (pageNumber: number) => void;
  selectedPages?: number[];
  reorderable?: boolean;
  onReorder?: (newOrder: number[]) => void;
}

export const PagePreview: React.FC<PagePreviewProps> = ({
  docId,
  onPageClick,
  selectedPages = [],
}) => {
  const [pages, setPages] = useState<{ page: number; preview_url: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function loadPreviews() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/preview/${docId}/pages`);
        if (!res.ok) throw new Error("No se pudieron cargar las previsualizaciones de páginas.");
        const data = await res.json();
        if (mounted) setPages(data.pages || []);
      } catch (err: any) {
        if (mounted) setError(err.message || "Error al cargar previsualización");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadPreviews();
    return () => {
      mounted = false;
    };
  }, [docId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-3" style={{ padding: "2rem" }}>
        <div className="loading-spinner" />
        <div className="text-muted mt-1" style={{ fontSize: "0.85rem" }}>
          Generando vistas previas de páginas...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ color: "var(--accent-warning)", fontSize: "0.85rem", padding: "1rem" }}>
        ⚠️ {error}
      </div>
    );
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
        gap: "1rem",
        padding: "1rem 0",
      }}
    >
      {pages.map((p) => {
        const isSelected = selectedPages.includes(p.page);
        return (
          <div
            key={p.page}
            onClick={() => onPageClick && onPageClick(p.page)}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              cursor: onPageClick ? "pointer" : "default",
              border: `2px solid ${isSelected ? "var(--accent-primary)" : "var(--border-subtle)"}`,
              borderRadius: "var(--radius-sm)",
              padding: "0.5rem",
              background: isSelected ? "var(--accent-muted)" : "var(--bg-surface)",
              transition: "all var(--transition-fast)",
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={api.previews.pageUrl(docId, p.page)}
              alt={`Página ${p.page}`}
              style={{
                width: "100%",
                height: "auto",
                aspectRatio: "1/1.414",
                objectFit: "contain",
                background: "#ffffff",
                borderRadius: "2px",
                boxShadow: "var(--shadow-sm)",
              }}
              loading="lazy"
            />
            <span
              style={{
                marginTop: "0.4rem",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: isSelected ? "var(--accent-primary)" : "var(--text-secondary)",
              }}
            >
              Pág. {p.page}
            </span>
          </div>
        );
      })}
    </div>
  );
};
