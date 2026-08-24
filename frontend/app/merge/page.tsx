"use client";

import React, { useEffect, useState } from "react";
import { api, Document, Operation } from "@/lib/api";
import { UploadZone } from "@/components/UploadZone";
import { DocumentCard } from "@/components/DocumentCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { WarningBanner } from "@/components/WarningBanner";
import { SuccessState } from "@/components/states/SuccessState";
import { LoadingState } from "@/components/states/LoadingState";
import { ErrorState } from "@/components/states/ErrorState";

export default function MergePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Operation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.documents.list().then((res) => setDocuments(res.documents || []));
  }, []);

  const toggleSelect = (id: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleMerge = async () => {
    if (selectedDocIds.length < 2) {
      alert("Selecciona al menos 2 PDFs para combinarlos.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const op = await api.merge(selectedDocIds);
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al unir PDFs");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <h1 className="page-title">Unir PDFs</h1>
        <SuccessState
          title="¡PDFs combinados correctamente!"
          description="Se ha generado un nuevo archivo con las páginas ordenadas de los documentos seleccionados."
          downloadUrl={api.downloadOperation("merge", result.id)}
          downloadFilename="documentos_unidos.pdf"
          sha256={result.output_sha256}
          onReset={() => {
            setResult(null);
            setSelectedDocIds([]);
          }}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Unir PDF</h1>
      <p className="page-subtitle">
        Combina múltiples archivos PDF en el orden exacto que selecciones. Los originales quedan inmutables.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Combinando archivos con pikepdf..." />}

      {!loading && !error && (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "2rem" }}>
          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              1. Selecciona los PDFs a unir ({selectedDocIds.length} seleccionados)
            </h2>

            {documents.length === 0 ? (
              <Card>
                <div style={{ padding: "1.5rem", textAlign: "center" }}>
                  <p className="text-muted mb-1">No hay documentos cargados.</p>
                </div>
              </Card>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {documents.map((doc) => {
                  const isSelected = selectedDocIds.includes(doc.id);
                  const orderIndex = selectedDocIds.indexOf(doc.id);
                  return (
                    <div
                      key={doc.id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.75rem",
                      }}
                    >
                      <div
                        style={{
                          width: "28px",
                          height: "28px",
                          borderRadius: "50%",
                          background: isSelected ? "var(--accent-primary)" : "var(--bg-elevated)",
                          color: isSelected ? "#fff" : "var(--text-muted)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontWeight: "bold",
                          fontSize: "0.8rem",
                          flexShrink: 0,
                        }}
                      >
                        {isSelected ? orderIndex + 1 : "○"}
                      </div>
                      <div style={{ flex: 1 }}>
                        <DocumentCard
                          document={doc}
                          selectable
                          selected={isSelected}
                          onSelect={() => toggleSelect(doc.id)}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div style={{ marginTop: "1.5rem" }}>
              <Button
                variant="primary"
                size="lg"
                disabled={selectedDocIds.length < 2}
                onClick={handleMerge}
              >
                📑 Combinar {selectedDocIds.length} Documentos
              </Button>
            </div>
          </div>

          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              2. O sube nuevos archivos
            </h2>
            <Card>
              <UploadZone
                onUploaded={(newDoc) => {
                  setDocuments((prev) => [newDoc, ...prev]);
                  setSelectedDocIds((prev) => [...prev, newDoc.id]);
                }}
              />
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
