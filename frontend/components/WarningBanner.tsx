import React from "react";

interface WarningBannerProps {
  type?: "warning" | "danger" | "info";
  title?: string;
  message: string;
  icon?: string;
}

export const WarningBanner: React.FC<WarningBannerProps> = ({
  type = "warning",
  title,
  message,
  icon,
}) => {
  const defaultIcon = type === "danger" ? "🛑" : type === "info" ? "ℹ️" : "⚠️";

  return (
    <div className={`warning-banner ${type}`}>
      <span className="warning-banner-icon">{icon || defaultIcon}</span>
      <div>
        {title && <strong style={{ display: "block", marginBottom: "2px" }}>{title}</strong>}
        <span>{message}</span>
      </div>
    </div>
  );
};
