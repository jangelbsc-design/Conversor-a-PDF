import React from "react";

interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = "📂",
  title,
  description,
  action,
}) => {
  return (
    <div className="state-container">
      <div className="state-icon">{icon}</div>
      <h3 className="state-title">{title}</h3>
      <p className="state-subtitle">{description}</p>
      {action && <div style={{ marginTop: "1rem" }}>{action}</div>}
    </div>
  );
};
