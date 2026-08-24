import React from "react";

interface LoadingStateProps {
  title?: string;
  description?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  title = "Procesando documento...",
  description = "Por favor espera mientras completamos la operación localmente.",
}) => {
  return (
    <div className="state-container">
      <div className="loading-spinner" />
      <h3 className="state-title" style={{ marginTop: "1rem" }}>{title}</h3>
      <p className="state-subtitle">{description}</p>
    </div>
  );
};
