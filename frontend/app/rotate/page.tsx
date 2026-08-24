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

export default function RotatePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [angle, setAngle] = useState(90);
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

  const handleRotate = async () => {
    if (!selectedDoc) return;
    setLoading(true);
    setError(null);
    try {
      const op = await api.rotate(selectedDoc.id, null, angle);
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al rotar PDF");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <h1 className="page-title">Rotar Páginas</h1>
        <SuccessState
          title="¡Páginas rotadas exitosamente!"
          description="Se ha ajustado el atributo /Rotate en el PDF versionado sin recodificar imágenes."
          downloadUrl={api.downloadOperation("rotate", result.id)}
          downloadFilename="documento_rotado.pdf"
          sha256={result.output_sha256}
          onReset={() => setResult(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Rotar Páginas</h1>
      <p className="page-subtitle">
        Gira todas las páginas de tu archivo PDF 90°, 180° o 270°.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Rotando páginas con pikepdf..." />}

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
              2. Ángulo de Giro
            </h2>

            {selectedDoc ? (
              <Card>
                <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
                  {[90, 180, 270].map((deg) => (
                    <Button
                      key={deg}
                      variant={angle === deg ? "primary" : "secondary"}
                      onClick={() => setAngle(deg)}
                    >
                      🔄 Girar {deg}°
                    </Button>
                  ))}
                </div>

                <div style={{ marginBottom: "1.5rem" }}>
                  <div className="text-muted" style={{ fontSize: "0.8rem", marginBottom: "0.5rem" }}>
                    Vista previa actual:
                  </div>
                  <PagePreview docId={selectedDoc.id} />
                </div>

                <Button variant="primary" size="lg" onClick={handleRotate}>
                  🔄 Aplicar Giro de {angle}° a Todas las Páginas
                </Button>
              </Card>
            ) : (
              <Card>
                <p className="text-muted">Selecciona un documento para rotar.</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
