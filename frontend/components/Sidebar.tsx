"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  name: string;
  href: string;
  icon: string;
  badge?: string;
}

const navTools: NavItem[] = [
  { name: "Unir PDF", href: "/merge", icon: "📑" },
  { name: "Dividir PDF", href: "/split", icon: "✂️" },
  { name: "Comprimir", href: "/compress", icon: "🗜️" },
  { name: "Convertir Office", href: "/convert", icon: "🔄" },
  { name: "Marca de Agua", href: "/watermark", icon: "💧" },
  { name: "Redactar / Ocultar", href: "/redact", icon: "⬛" },
  { name: "OCR Reconocimiento", href: "/ocr", icon: "🔍" },
  { name: "Rotar Páginas", href: "/rotate", icon: "🔄" },
  { name: "Reordenar", href: "/reorder", icon: "↕️" },
  { name: "Firmar (Local)", href: "/sign", icon: "✍️", badge: "Personal" },
];

const navSystem: NavItem[] = [
  { name: "Documentos", href: "/", icon: "📁" },
  { name: "Auditoría & Logs", href: "/audit", icon: "📜" },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="app-sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">📄</div>
        <div>
          <div className="sidebar-logo-text">PDF Suite Local</div>
          <div className="sidebar-logo-sub">100% On-Premise</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">General</div>
        {navSystem.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-item ${isActive ? "active" : ""}`}
            >
              <span className="sidebar-item-icon">{item.icon}</span>
              <span style={{ flex: 1 }}>{item.name}</span>
            </Link>
          );
        })}

        <div className="sidebar-section-label" style={{ marginTop: "0.5rem" }}>
          Herramientas PDF
        </div>
        {navTools.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-item ${isActive ? "active" : ""}`}
            >
              <span className="sidebar-item-icon">{item.icon}</span>
              <span style={{ flex: 1 }}>{item.name}</span>
              {item.badge && (
                <span
                  style={{
                    fontSize: "0.65rem",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "4px",
                    background: "rgba(245, 158, 11, 0.2)",
                    color: "var(--accent-warning)",
                  }}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
          🔒 <strong>Sin nube ni telemetría</strong>
          <div style={{ marginTop: "2px" }}>Archivos guardados en tu máquina.</div>
        </div>
      </div>
    </aside>
  );
};
