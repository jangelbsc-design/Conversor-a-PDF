"use client";

import React, { useRef, useState } from "react";
import { api, Document } from "../lib/api";

interface UploadZoneProps {
  onUploaded: (doc: Document) => void;
  accept?: string;
  maxFiles?: number;
  label?: string;
  description?: string;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onUploaded,
  accept = ".pdf,.docx,.xlsx,.pptx,.odt,.txt",
  label = "Arrastra y suelta tu archivo aquí",
  description = "o haz clic para seleccionar (PDF, Word, Excel, PowerPoint, ODT)",
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError(null);
    setUploading(true);

    try {
      const file = files[0];
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(api.documents.uploadUrl(), {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        let msg = "Error al subir archivo";
        try {
          const errJson = await res.json();
          msg = errJson.detail || msg;
        } catch {
          // ignore
        }
        throw new Error(msg);
      }

      const doc: Document = await res.json();
      onUploaded(doc);
    } catch (err: any) {
      setError(err.message || "Error desconocido al procesar archivo.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div
        className={`upload-zone ${isDragging ? "drag-over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          style={{ display: "none" }}
          onChange={(e) => handleFiles(e.target.files)}
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-1">
            <div className="loading-spinner" />
            <div style={{ marginTop: "0.5rem", fontWeight: 500 }}>
              Cargando e inspeccionando documento...
            </div>
            <div className="text-muted" style={{ fontSize: "0.8rem" }}>
              Analizando fuentes, formularios, firmas y cifrado
            </div>
          </div>
        ) : (
          <>
            <div className="upload-zone-icon">📤</div>
            <div className="upload-zone-title">{label}</div>
            <div className="upload-zone-subtitle">{description}</div>
          </>
        )}
      </div>

      {error && (
        <div style={{ marginTop: "0.75rem", color: "var(--accent-danger)", fontSize: "0.85rem" }}>
          ⚠️ {error}
        </div>
      )}
    </div>
  );
};
