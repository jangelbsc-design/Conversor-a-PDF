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

export default function RedactPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [page, setPage] = useState(1);
  const [x, setX] = useState(50);
  const [y, setY] = useState(700);
  const [width, setWidth] = useState(200);
  const [height, setHeight] = useState(40);
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

  const handleRedact = async () => {
    if (!selectedDoc) return;
    setLoading(true);
    setError(null);

    const region = { page, x, y, width, height };

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/redact/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_id: selectedDoc.id,
          regions: [region],
        }),
      });

      if (!res.ok) {
        let msg = "Error al redactar.";
        try {
          const j = await res.json();
          msg = j.detail || msg;
        } catch {}
        throw new Error(msg);
      }

      const op: Operation = await res.json();
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al aplicar redacción");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <h1 className="page-title">Redactar / Ocultar Información</h1>
        <SuccessState
          title="¡Región redactada con éxito!"
          description="Se ha colocado un rectángulo opaco en las coordenadas especificadas."
          downloadUrl={api.downloadOperation("redact", result.id)}
          downloadFilename="documento_redactado.pdf"
          sha256={result.output_sha256}
          onReset={() => setResult(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Redactar / Ocultar Información</h1>
      <p className="page-subtitle">
        Cubre y oculta partes sensibles del PDF con rectángulos opacos.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Insertando cajas de redacción..." />}

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
              2. Coordenadas de la región
            </h2>

            {selectedDoc ? (
              <Card>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
                  <div className="input-group">
                    <label className="input-label">Página (1-indexed):</label>
                    <input
                      type="number"
                      min="1"
                      max={selectedDoc.page_count || 100}
                      className="input"
                      value={page}
                      onChange={(e) => setPage(parseInt(e.target.value, 10))}
                    />
                  </div>
                  <div className="input-group">
                    <label className="input-label">X (puntos PDF):</label>
                    <input
                      type="number"
                      className="input"
                      value={x}
                      onChange={(e) => setX(parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Y (desde abajo):</label>
                    <input
                      type="number"
                      className="input"
                      value={y}
                      onChange={(e) => setY(parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Ancho (Width):</label>
                    <input
                      type="number"
                      className="input"
                      value={width}
                      onChange={(e) => setWidth(parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Alto (Height):</label>
                    <input
                      type="number"
                      className="input"
                      value={height}
                      onChange={(e) => setHeight(parseFloat(e.target.value))}
                    />
                  </div>
                </div>

                <Button variant="danger" size="lg" onClick={handleRedact}>
                  ⬛ Aplicar Recuadro de Redacción
                </Button>
              </Card>
            ) : (
              <Card>
                <p className="text-muted">Selecciona un documento para redactar.</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
