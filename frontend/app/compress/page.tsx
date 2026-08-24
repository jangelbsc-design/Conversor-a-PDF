"use client";

import React, { useEffect, useState } from "react";
import { api, Document, Operation } from "@/lib/api";
import { UploadZone } from "@/components/UploadZone";
import { DocumentCard } from "@/components/DocumentCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SuccessState } from "@/components/states/SuccessState";
import { LoadingState } from "@/components/states/LoadingState";
import { ErrorState } from "@/components/states/ErrorState";

export default function CompressPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [level, setLevel] = useState<1 | 2 | 3>(2);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Operation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.documents.list().then((res) => {
      const docs = res.documents || [];
      setDocuments(docs);
      if (docs.length > 0) setSelectedDoc(docs[0]);
    });
  }, []);

  const handleCompress = async () => {
    if (!selectedDoc) return;
    setLoading(true);
    setError(null);
    try {
      const op = await api.compress(selectedDoc.id, level);
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al comprimir PDF");
    } finally {
      setLoading(false);
    }
  };

  const reduction = result?.params_json?.reduction_percent;

  if (result) {
    return (
      <div>
        <h1 className="page-title">Comprimir PDF</h1>
        <SuccessState
          title={`¡PDF comprimido! ${reduction !== undefined ? `(-${reduction}%)` : ""}`}
          description="Se ha generado un nuevo archivo con flate streams optimizados."
          downloadUrl={api.downloadOperation("compress", result.id)}
          downloadFilename="documento_comprimido.pdf"
          sha256={result.output_sha256}
          onReset={() => setResult(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Comprimir PDF</h1>
      <p className="page-subtitle">
        Reduce el tamaño de tu archivo PDF manteniendo la máxima legibilidad posible.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Comprimiendo streams con pikepdf..." />}

      {!loading && !error && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              1. Selecciona documento
            </h2>

            <Card style={{ marginBottom: "1.5rem" }}>
              <UploadZone
                onUploaded={(newDoc) => {
                  setDocuments((prev) => [newDoc, ...prev]);
                  setSelectedDoc(newDoc);
                }}
              />
            </Card>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "250px", overflowY: "auto" }}>
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  selectable
                  selected={selectedDoc?.id === doc.id}
                  onSelect={(d) => setSelectedDoc(d)}
                />
              ))}
            </div>
          </div>

          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              2. Nivel de Compresión
            </h2>

            {selectedDoc ? (
              <Card>
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "1.5rem" }}>
                  <label
                    style={{
                      display: "flex",
                      gap: "0.75rem",
                      padding: "0.75rem",
                      borderRadius: "var(--radius-sm)",
                      background: level === 1 ? "var(--accent-muted)" : "var(--bg-elevated)",
                      border: `1px solid ${level === 1 ? "var(--accent-primary)" : "var(--border-subtle)"}`,
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="radio"
                      name="compLevel"
                      checked={level === 1}
                      onChange={() => setLevel(1)}
                    />
                    <div>
                      <strong style={{ display: "block", fontSize: "0.9rem" }}>Ligera</strong>
                      <span className="text-muted" style={{ fontSize: "0.8rem" }}>
                        Preserva calidad máxima de imágenes y fuentes.
                      </span>
                    </div>
                  </label>

                  <label
                    style={{
                      display: "flex",
                      gap: "0.75rem",
                      padding: "0.75rem",
                      borderRadius: "var(--radius-sm)",
                      background: level === 2 ? "var(--accent-muted)" : "var(--bg-elevated)",
                      border: `1px solid ${level === 2 ? "var(--accent-primary)" : "var(--border-subtle)"}`,
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="radio"
                      name="compLevel"
                      checked={level === 2}
                      onChange={() => setLevel(2)}
                    />
                    <div>
                      <strong style={{ display: "block", fontSize: "0.9rem" }}>Media (Recomendada)</strong>
                      <span className="text-muted" style={{ fontSize: "0.8rem" }}>
                        Equilibrio ideal entre reducción de bytes y calidad visual.
                      </span>
                    </div>
                  </label>

                  <label
                    style={{
                      display: "flex",
                      gap: "0.75rem",
                      padding: "0.75rem",
                      borderRadius: "var(--radius-sm)",
                      background: level === 3 ? "var(--accent-muted)" : "var(--bg-elevated)",
                      border: `1px solid ${level === 3 ? "var(--accent-primary)" : "var(--border-subtle)"}`,
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="radio"
                      name="compLevel"
                      checked={level === 3}
                      onChange={() => setLevel(3)}
                    />
                    <div>
                      <strong style={{ display: "block", fontSize: "0.9rem" }}>Agresiva</strong>
                      <span className="text-muted" style={{ fontSize: "0.8rem" }}>
                        Máxima compresión mediante compresión profunda de streams de objetos.
                      </span>
                    </div>
                  </label>
                </div>

                <Button variant="primary" size="lg" onClick={handleCompress}>
                  🗜️ Comprimir PDF Ahora
                </Button>
              </Card>
            ) : (
              <Card>
                <p className="text-muted">Selecciona un documento para comprimir.</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
