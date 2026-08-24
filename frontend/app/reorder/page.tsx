"use client";

import React, { useEffect, useState } from "react";
import { api, Document, Operation } from "@/lib/api";
import { UploadZone } from "@/components/UploadZone";
import { DocumentCard } from "@/components/DocumentCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PagePreview } from "@/components/PagePreview";
import { SuccessState } from "@/components/states/SuccessState";
import { LoadingState } from "@/components/states/LoadingState";
import { ErrorState } from "@/components/states/ErrorState";

export default function ReorderPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [orderText, setOrderText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Operation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.documents.list().then((res) => {
      const docs = res.documents || [];
      setDocuments(docs);
      if (docs.length > 0) {
        setSelectedDoc(docs[0]);
        if (docs[0].page_count) {
          setOrderText(Array.from({ length: docs[0].page_count }, (_, i) => i + 1).join(", "));
        }
      }
    });
  }, []);

  const handleDocSelect = (doc: Document) => {
    setSelectedDoc(doc);
    if (doc.page_count) {
      setOrderText(Array.from({ length: doc.page_count }, (_, i) => i + 1).join(", "));
    }
  };

  const handleReorder = async () => {
    if (!selectedDoc) return;
    setLoading(true);
    setError(null);

    try {
      const newOrder = orderText.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n));
      if (newOrder.length === 0) throw new Error("Debes indicar una secuencia válida de páginas.");
      const op = await api.reorder(selectedDoc.id, newOrder);
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al reordenar páginas");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <h1 className="page-title">Reordenar Páginas</h1>
        <SuccessState
          title="¡Páginas reordenadas con éxito!"
          description="Se ha estructurado un nuevo archivo siguiendo exactamente la secuencia indicada."
          downloadUrl={api.downloadOperation("reorder", result.id)}
          downloadFilename="documento_reordenado.pdf"
          sha256={result.output_sha256}
          onReset={() => setResult(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Reordenar Páginas</h1>
      <p className="page-subtitle">
        Modifica el orden de las páginas o duplica páginas clave escribiendo el nuevo orden de secuencia.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Reorganizando páginas con pikepdf..." />}

      {!loading && !error && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "2rem" }}>
          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              1. Selecciona documento
            </h2>

            <Card style={{ marginBottom: "1.5rem" }}>
              <UploadZone
                onUploaded={(newDoc) => {
                  setDocuments((prev) => [newDoc, ...prev]);
                  handleDocSelect(newDoc);
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
                  onSelect={(d) => handleDocSelect(d)}
                />
              ))}
            </div>
          </div>

          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              2. Nuevo orden de secuencia
            </h2>

            {selectedDoc ? (
              <Card>
                <div className="input-group" style={{ marginBottom: "1.5rem" }}>
                  <label className="input-label">
                    Orden de páginas (separado por comas, ej: 3, 1, 2, 2):
                  </label>
                  <input
                    className="input"
                    value={orderText}
                    onChange={(e) => setOrderText(e.target.value)}
                  />
                  <span className="text-muted" style={{ fontSize: "0.75rem" }}>
                    Total páginas originales: {selectedDoc.page_count || "?"}
                  </span>
                </div>

                <div style={{ marginBottom: "1.5rem" }}>
                  <div className="text-muted" style={{ fontSize: "0.8rem", marginBottom: "0.5rem" }}>
                    Páginas disponibles:
                  </div>
                  <PagePreview docId={selectedDoc.id} />
                </div>

                <Button variant="primary" size="lg" onClick={handleReorder}>
                  ↕️ Reordenar y Generar PDF
                </Button>
              </Card>
            ) : (
              <Card>
                <p className="text-muted">Selecciona un documento para reordenar.</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
