import React from "react";
import { Button } from "../ui/Button";

interface SuccessStateProps {
  title?: string;
  description?: string;
  downloadUrl?: string;
  downloadFilename?: string;
  sha256?: string | null;
  onReset?: () => void;
}

export const SuccessState: React.FC<SuccessStateProps> = ({
  title = "¡Operación completada con éxito!",
  description = "Tu archivo transformado está listo y versionado en el almacenamiento local.",
  downloadUrl,
  downloadFilename,
  sha256,
  onReset,
}) => {
  return (
    <div className="state-container">
      <div className="state-icon" style={{ color: "var(--accent-success)" }}>✅</div>
      <h3 className="state-title">{title}</h3>
      <p className="state-subtitle">{description}</p>

      {sha256 && (
        <div style={{ marginTop: "0.5rem", maxWidth: "500px", wordBreak: "break-all" }}>
          <span className="text-muted" style={{ fontSize: "0.75rem" }}>SHA-256 Output: </span>
          <code className="text-mono" style={{ fontSize: "0.75rem", color: "var(--accent-info)" }}>
            {sha256}
          </code>
        </div>
      )}

      <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem" }}>
        {downloadUrl && (
          <a
            href={downloadUrl}
            download={downloadFilename}
            className="btn btn-primary btn-lg"
          >
            📥 Descargar archivo
          </a>
        )}
        {onReset && (
          <Button variant="secondary" onClick={onReset}>
            Procesar otro
          </Button>
        )}
      </div>
    </div>
  );
};
