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

export default function OCRPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [language, setLanguage] = useState("spa");
  const [deskew, setDeskew] = useState(true);
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

  const handleOCR = async () => {
    if (!selectedDoc) return;
    setLoading(true);
    setError(null);
    try {
      const op = await api.ocr(selectedDoc.id, language);
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al aplicar OCR");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <h1 className="page-title">Reconocimiento Óptico (OCR)</h1>
        <SuccessState
          title="¡Capa de texto OCR insertada con éxito!"
          description="Ahora puedes buscar, seleccionar y copiar texto dentro del PDF generado."
          downloadUrl={api.downloadOperation("ocr", result.id)}
          downloadFilename="documento_ocr.pdf"
          sha256={result.output_sha256}
          onReset={() => setResult(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Reconocimiento Óptico de Caracteres (OCR)</h1>
      <p className="page-subtitle">
        Convierte documentos PDF escaneados o imágenes en archivos PDF con capa de texto buscable mediante Tesseract.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Ejecutando OCR con Tesseract & ocrmypdf..." />}

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
              2. Parámetros de Reconocimiento
            </h2>

            {selectedDoc ? (
              <Card>
                <div className="input-group" style={{ marginBottom: "1.25rem" }}>
                  <label className="input-label">Idioma del documento:</label>
                  <select
                    className="input"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                  >
                    <option value="spa+eng">Español + Inglés (Recomendado)</option>
                    <option value="spa">Solo Español</option>
                    <option value="eng">Solo Inglés</option>
                  </select>
                </div>

                <div style={{ marginBottom: "1.5rem" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={deskew}
                      onChange={(e) => setDeskew(e.target.checked)}
                    />
                    <span style={{ fontSize: "0.85rem" }}>
                      Enderezar páginas inclinadas automáticamente (Deskew)
                    </span>
                  </label>
                </div>

                <Button variant="primary" size="lg" onClick={handleOCR}>
                  🔍 Iniciar Proceso OCR
                </Button>
              </Card>
            ) : (
              <Card>
                <p className="text-muted">Selecciona un documento para aplicar OCR.</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
