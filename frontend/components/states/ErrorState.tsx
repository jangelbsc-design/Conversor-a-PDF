import React from "react";
import { Button } from "../ui/Button";

interface ErrorStateProps {
  title?: string;
  error: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Ocurrió un error",
  error,
  onRetry,
}) => {
  return (
    <div className="state-container">
      <div className="state-icon" style={{ color: "var(--accent-danger)" }}>⚠️</div>
      <h3 className="state-title">{title}</h3>
      <p className="state-subtitle" style={{ color: "var(--accent-danger)" }}>
        {error}
      </p>
      {onRetry && (
        <div style={{ marginTop: "1.5rem" }}>
          <Button variant="secondary" onClick={onRetry}>
            Intentar nuevamente
          </Button>
        </div>
      )}
    </div>
  );
};
