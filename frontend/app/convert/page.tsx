"use client";

import React, { useState } from "react";
import { api, Operation } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SuccessState } from "@/components/states/SuccessState";
import { LoadingState } from "@/components/states/LoadingState";
import { ErrorState } from "@/components/states/ErrorState";

export default function ConvertPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Operation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleConvert = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/convert/`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        let msg = "Error al convertir documento.";
        try {
          const json = await res.json();
          msg = json.detail || msg;
        } catch {}
        throw new Error(msg);
      }

      const op: Operation = await res.json();
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al procesar archivo en LibreOffice.");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <h1 className="page-title">Convertir a PDF</h1>
        <SuccessState
          title="¡Documento convertido a PDF con éxito!"
          description="Generado localmente mediante LibreOffice headless."
          downloadUrl={api.downloadOperation("convert", result.id)}
          downloadFilename={`${file?.name.replace(/\.[^/.]+$/, "")}.pdf`}
          sha256={result.output_sha256}
          onReset={() => {
            setResult(null);
            setFile(null);
          }}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Convertir Office a PDF</h1>
      <p className="page-subtitle">
        Convierte archivos Word (.docx, .doc), Excel (.xlsx, .xls), PowerPoint (.pptx, .ppt) y ODT a PDF localmente vía LibreOffice.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Convirtiendo con LibreOffice headless en sandbox..." />}

      {!loading && !error && (
        <Card style={{ maxWidth: "600px" }}>
          <div style={{ marginBottom: "1.5rem" }}>
            <label className="input-label" style={{ marginBottom: "0.5rem", display: "block" }}>
              Selecciona tu archivo de Microsoft Office u OpenDocument:
            </label>
            <input
              type="file"
              accept=".docx,.doc,.xlsx,.xls,.pptx,.ppt,.odt,.ods,.odp,.rtf,.txt"
              className="input"
              onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
            />
          </div>

          {file && (
            <div style={{ marginBottom: "1.5rem", padding: "0.75rem", background: "var(--bg-elevated)", borderRadius: "var(--radius-sm)" }}>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>📄 {file.name}</div>
              <div className="text-muted" style={{ fontSize: "0.8rem" }}>
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </div>
            </div>
          )}

          <Button variant="primary" size="lg" disabled={!file} onClick={handleConvert}>
            🔄 Convertir a PDF
          </Button>
        </Card>
      )}
    </div>
  );
}
