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

export default function WatermarkPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [text, setText] = useState("CONFIDENCIAL");
  const [opacity, setOpacity] = useState(0.3);
  const [rotation, setRotation] = useState(45);
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

  const handleWatermark = async () => {
    if (!selectedDoc || !text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const op = await api.watermark(selectedDoc.id, text, opacity, rotation);
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al aplicar marca de agua");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <h1 className="page-title">Marca de Agua</h1>
        <SuccessState
          title="¡Marca de agua aplicada exitosamente!"
          description="Se ha insertado el texto diagonal en todas las páginas sin alterar los originales."
          downloadUrl={api.downloadOperation("watermark", result.id)}
          downloadFilename="documento_watermark.pdf"
          sha256={result.output_sha256}
          onReset={() => setResult(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Añadir Marca de Agua</h1>
      <p className="page-subtitle">
        Inserta un sello o texto diagonal personalizado en cada página de tu documento.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Insertando streams de marca de agua..." />}

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
              2. Personalizar Texto
            </h2>

            {selectedDoc ? (
              <Card>
                <div className="input-group" style={{ marginBottom: "1.25rem" }}>
                  <label className="input-label">Texto de la marca de agua:</label>
                  <input
                    className="input"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Ej: COPIA NO OFICIAL, BORRADOR, CONFIDENCIAL"
                  />
                </div>

                <div className="input-group" style={{ marginBottom: "1.25rem" }}>
                  <div className="flex justify-between">
                    <label className="input-label">Opacidad: {Math.round(opacity * 100)}%</label>
                  </div>
                  <input
                    type="range"
                    min="0.05"
                    max="1"
                    step="0.05"
                    value={opacity}
                    onChange={(e) => setOpacity(parseFloat(e.target.value))}
                    className="range-slider"
                  />
                </div>

                <div className="input-group" style={{ marginBottom: "1.5rem" }}>
                  <div className="flex justify-between">
                    <label className="input-label">Ángulo de rotación: {rotation}°</label>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="360"
                    step="15"
                    value={rotation}
                    onChange={(e) => setRotation(parseInt(e.target.value, 10))}
                    className="range-slider"
                  />
                </div>

                <Button variant="primary" size="lg" disabled={!text.trim()} onClick={handleWatermark}>
                  💧 Aplicar Marca de Agua
                </Button>
              </Card>
            ) : (
              <Card>
                <p className="text-muted">Selecciona un documento para aplicar marca de agua.</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
