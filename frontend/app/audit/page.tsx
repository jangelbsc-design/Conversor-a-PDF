"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AuditLogViewer } from "@/components/AuditLog";
import { Card } from "@/components/ui/Card";
import { WarningBanner } from "@/components/WarningBanner";

export default function AuditPage() {
  const [stats, setStats] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    api.backupStats().then((data) => setStats(data)).catch(() => {});
  }, []);

  const formatBytes = (bytes?: number) => {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <div>
          <h1 className="page-title">Registro de Auditoría (Audit Log)</h1>
          <p className="page-subtitle">
            Log append-only inmutable con marcas de tiempo UTC, hashes SHA-256 antes y después de cada transformación.
          </p>
        </div>
        <a href={api.backupUrl()} className="btn btn-primary btn-sm" download>
          📦 Descargar Backup Completo (ZIP)
        </a>
      </div>

      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "2rem" }}>
          <Card>
            <div className="text-muted" style={{ fontSize: "0.75rem" }}>Originales Inmutables</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, marginTop: "0.25rem" }}>
              {stats.originals_count} archivos
            </div>
            <div className="text-muted" style={{ fontSize: "0.75rem" }}>{formatBytes(stats.originals_size_bytes)}</div>
          </Card>
          <Card>
            <div className="text-muted" style={{ fontSize: "0.75rem" }}>Outputs Versionados</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, marginTop: "0.25rem" }}>
              {stats.outputs_count} archivos
            </div>
            <div className="text-muted" style={{ fontSize: "0.75rem" }}>{formatBytes(stats.outputs_size_bytes)}</div>
          </Card>
          <Card>
            <div className="text-muted" style={{ fontSize: "0.75rem" }}>Log de Auditoría</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, marginTop: "0.25rem" }}>
              audit.jsonl
            </div>
            <div className="text-muted" style={{ fontSize: "0.75rem" }}>{formatBytes(stats.audit_log_size_bytes)}</div>
          </Card>
          <Card>
            <div className="text-muted" style={{ fontSize: "0.75rem" }}>Almacenamiento Total</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, marginTop: "0.25rem", color: "var(--accent-primary)" }}>
              {formatBytes(stats.total_size_bytes)}
            </div>
            <div className="text-muted" style={{ fontSize: "0.75rem" }}>En tu disco local</div>
          </Card>
        </div>
      )}

      <Card>
        <AuditLogViewer />
      </Card>
    </div>
  );
}
