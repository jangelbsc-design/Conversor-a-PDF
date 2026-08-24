import React from "react";
import { Document } from "../lib/api";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

interface DocumentCardProps {
  document: Document;
  onSelect?: (doc: Document) => void;
  onDelete?: (id: string) => void;
  selected?: boolean;
  selectable?: boolean;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onSelect,
  onDelete,
  selected = false,
  selectable = false,
}) => {
  const formatBytes = (bytes: number | null) => {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return iso;
    }
  };

  return (
    <div
      className={`doc-card ${selected ? "selected" : ""}`}
      style={{
        borderColor: selected ? "var(--accent-primary)" : undefined,
        background: selected ? "var(--accent-muted)" : undefined,
        cursor: selectable ? "pointer" : "default",
      }}
      onClick={() => selectable && onSelect && onSelect(document)}
    >
      <div className="doc-card-icon">📄</div>
      <div className="doc-card-info">
        <div className="flex items-center gap-1">
          <div className="doc-card-name">{document.original_filename}</div>
          {document.page_count !== null && (
            <Badge variant="neutral">{document.page_count} pág.</Badge>
          )}
          {document.is_encrypted && <Badge variant="danger">Cifrado</Badge>}
          {document.has_forms && <Badge variant="warning">Formulario</Badge>}
          {document.has_signatures && <Badge variant="warning">Firmado</Badge>}
        </div>

        <div className="doc-card-meta">
          <span>{formatBytes(document.size_bytes)}</span>
          <span>•</span>
          <span>{formatDate(document.created_at)}</span>
          <span>•</span>
          <span title={document.sha256} style={{ fontFamily: "monospace", fontSize: "0.7rem" }}>
            SHA: {document.sha256.substring(0, 10)}...
          </span>
        </div>

        {document.warnings && document.warnings.length > 0 && (
          <div style={{ marginTop: "0.4rem", display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            {document.warnings.map((w, idx) => (
              <span
                key={idx}
                style={{
                  fontSize: "0.7rem",
                  color: w.severity === "error" ? "var(--accent-danger)" : "var(--accent-warning)",
                }}
              >
                ⚠️ {w.message}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1">
        {onDelete && (
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(document.id);
            }}
            title="Eliminar documento"
          >
            🗑️
          </Button>
        )}
      </div>
    </div>
  );
};
