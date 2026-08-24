import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  elevated = false,
  className = "",
  ...props
}) => {
  return (
    <div
      className={`card ${elevated ? "card-elevated" : ""} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
