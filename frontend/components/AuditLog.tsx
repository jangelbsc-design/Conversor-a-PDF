"use client";

import React, { useEffect, useState } from "react";
import { api, AuditEvent } from "../lib/api";
import { Badge } from "./ui/Badge";
import { LoadingState } from "./states/LoadingState";
import { EmptyState } from "./states/EmptyState";

export const AuditLogViewer: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLog = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.audit(200);
      setEvents(res.events || []);
    } catch (err: any) {
      setError(err.message || "Error al cargar log de auditoría.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLog();
  }, []);

  const getBadgeVariant = (eventType: string) => {
    if (eventType.includes("UPLOADED") || eventType.includes("COMPLETED")) return "success";
    if (eventType.includes("DELETED")) return "danger";
    if (eventType.includes("SEALED")) return "info";
    return "neutral";
  };

  if (loading) return <LoadingState title="Cargando log de auditoría..." />;
  if (error) return <div style={{ color: "var(--accent-danger)" }}>⚠️ {error}</div>;
  if (events.length === 0) {
    return (
      <EmptyState
        icon="📜"
        title="Sin eventos registrados aún"
        description="Las operaciones de subida, transformación y sellado se registrarán de manera append-only aquí."
      />
    );
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="audit-table">
        <thead>
          <tr>
            <th>Fecha / Hora (UTC)</th>
            <th>Tipo de Evento</th>
            <th>Documento / Operación</th>
            <th>SHA-256 Previo</th>
            <th>SHA-256 Resultante</th>
            <th>Actor / IP</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.id}>
              <td style={{ whiteSpace: "nowrap" }}>
                {new Date(e.timestamp).toLocaleString()}
              </td>
              <td>
                <Badge variant={getBadgeVariant(e.event_type)}>{e.event_type}</Badge>
              </td>
              <td>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {e.doc_id ? `Doc: ${e.doc_id.substring(0, 8)}...` : ""}
                  {e.operation_id ? ` Op: ${e.operation_id.substring(0, 8)}...` : ""}
                </div>
              </td>
              <td className="audit-hash">
                {e.sha256_before ? `${e.sha256_before.substring(0, 12)}...` : "—"}
              </td>
              <td className="audit-hash">
                {e.sha256_after ? `${e.sha256_after.substring(0, 12)}...` : "—"}
              </td>
              <td>
                <span style={{ fontSize: "0.75rem" }}>{e.actor}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
