"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api, Document } from "@/lib/api";
import { UploadZone } from "@/components/UploadZone";
import { DocumentCard } from "@/components/DocumentCard";
import { WarningBanner } from "@/components/WarningBanner";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/states/EmptyState";
import { LoadingState } from "@/components/states/LoadingState";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.documents.list();
      setDocuments(res.documents || []);
    } catch (err: any) {
      setError(err.message || "Error al conectar con el backend local.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("¿Deseas marcar este documento como eliminado?")) return;
    try {
      await api.documents.delete(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err: any) {
      alert("Error al eliminar: " + err.message);
    }
  };

  const tools = [
    { title: "Unir PDF", href: "/merge", icon: "📑", desc: "Combina varios archivos en un único PDF ordenado." },
    { title: "Dividir PDF", href: "/split", icon: "✂️", desc: "Extrae rangos de páginas o genera un PDF por página." },
    { title: "Comprimir", href: "/compress", icon: "🗜️", desc: "Reduce el peso en MB sin perder legibilidad." },
    { title: "Convertir Office", href: "/convert", icon: "🔄", desc: "Word, Excel, PowerPoint a PDF vía LibreOffice." },
    { title: "Marca de Agua", href: "/watermark", icon: "💧", desc: "Añade texto personalizado con transparencia." },
    { title: "Redactar", href: "/redact", icon: "⬛", desc: "Oculta áreas con recuadros opacos de protección." },
    { title: "OCR", href: "/ocr", icon: "🔍", desc: "Convierte documentos escaneados en texto buscable." },
    { title: "Rotar", href: "/rotate", icon: "🔄", desc: "Gira páginas 90°, 180° o 270° fácilmente." },
    { title: "Reordenar", href: "/reorder", icon: "↕️", desc: "Cambia el orden de páginas arrastrando." },
    { title: "Firma (Local)", href: "/sign", icon: "✍️", desc: "Campos, consentimiento local y sellado SHA-256." },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <div>
          <h1 className="page-title">Suite PDF Local</h1>
          <p className="page-subtitle">
            Almacenamiento y procesamiento 100% en tu equipo. Sin subir datos a la nube.
          </p>
        </div>
        <a href={api.backupUrl()} className="btn btn-secondary btn-sm" download>
          📦 Exportar Backup Completo (ZIP)
        </a>
      </div>

      <div style={{ marginBottom: "2.5rem" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "1rem" }}>
          Herramientas Rápidas
        </h2>
        <div className="tool-grid">
          {tools.map((t) => (
            <Link key={t.href} href={t.href} className="tool-card">
              <div className="tool-card-icon" style={{ background: "var(--accent-muted)" }}>
                {t.icon}
              </div>
              <div className="tool-card-name">{t.title}</div>
              <div className="tool-card-desc">{t.desc}</div>
            </Link>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
        <div>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "1rem" }}>
            Subir Nuevo Archivo
          </h2>
          <Card>
            <UploadZone
              onUploaded={(newDoc) => {
                setDocuments((prev) => [newDoc, ...prev]);
              }}
            />
          </Card>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>
              Documentos Locales ({documents.length})
            </h2>
            <Button variant="ghost" size="sm" onClick={loadDocuments}>
              🔄 Actualizar
            </Button>
          </div>

          {loading ? (
            <LoadingState title="Cargando biblioteca..." />
          ) : error ? (
            <div style={{ color: "var(--accent-danger)", fontSize: "0.9rem" }}>⚠️ {error}</div>
          ) : documents.length === 0 ? (
            <Card>
              <EmptyState
                icon="📄"
                title="Sin documentos aún"
                description="Sube archivos usando la zona de la izquierda para comenzar."
              />
            </Card>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "450px", overflowY: "auto" }}>
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
