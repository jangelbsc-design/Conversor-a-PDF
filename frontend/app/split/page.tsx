"use client";

import React, { useEffect, useState } from "react";
import { api, Document, Operation } from "@/lib/api";
import { UploadZone } from "@/components/UploadZone";
import { DocumentCard } from "@/components/DocumentCard";
import { PagePreview } from "@/components/PagePreview";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SuccessState } from "@/components/states/SuccessState";
import { LoadingState } from "@/components/states/LoadingState";
import { ErrorState } from "@/components/states/ErrorState";

export default function SplitPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [splitMode, setSplitMode] = useState<"range" | "all">("all");
  const [rangesText, setRangesText] = useState("1-2, 3-4");
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

  const handleSplit = async () => {
    if (!selectedDoc) return;
    setLoading(true);
    setError(null);

    try {
      let pageRanges: number[][] | undefined = undefined;
      if (splitMode === "range") {
        // Parsear "1-3, 4-5" a [[1, 3], [4, 5]]
        pageRanges = rangesText.split(",").map((part) => {
          const trimmed = part.trim();
          if (trimmed.includes("-")) {
            const [s, e] = trimmed.split("-").map((n) => parseInt(n.trim(), 10));
            return [s, e];
          }
          const p = parseInt(trimmed, 10);
          return [p, p];
        });
      }

      const op = await api.split(selectedDoc.id, pageRanges, splitMode === "all");
      setResult(op);
    } catch (err: any) {
      setError(err.message || "Error al dividir PDF");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <h1 className="page-title">Dividir PDF</h1>
        <SuccessState
          title="¡PDF dividido exitosamente!"
          description="Los archivos resultantes se han empaquetado y versionado en el almacenamiento local."
          downloadUrl={api.downloadOperation("split", result.id)}
          downloadFilename="documentos_divididos.zip"
          sha256={result.output_sha256}
          onReset={() => setResult(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Dividir PDF</h1>
      <p className="page-subtitle">
        Separa páginas en archivos independientes o por rangos específicos.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Dividiendo páginas con pikepdf..." />}

      {!loading && !error && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "2rem" }}>
          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              1. Selecciona o sube un documento
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
              2. Configurar corte
            </h2>

            {selectedDoc ? (
              <Card>
                <div style={{ marginBottom: "1.5rem" }}>
                  <label className="input-label" style={{ marginBottom: "0.5rem", display: "block" }}>
                    Modo de división:
                  </label>
                  <div style={{ display: "flex", gap: "1rem" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", cursor: "pointer" }}>
                      <input
                        type="radio"
                        checked={splitMode === "all"}
                        onChange={() => setSplitMode("all")}
                      />
                      <span>Extraer todas las páginas (1 PDF por página)</span>
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", cursor: "pointer" }}>
                      <input
                        type="radio"
                        checked={splitMode === "range"}
                        onChange={() => setSplitMode("range")}
                      />
                      <span>Por rangos de páginas</span>
                    </label>
                  </div>
                </div>

                {splitMode === "range" && (
                  <div className="input-group" style={{ marginBottom: "1.5rem" }}>
                    <label className="input-label">Rangos de páginas (ej: 1-3, 5, 6-8):</label>
                    <input
                      className="input"
                      value={rangesText}
                      onChange={(e) => setRangesText(e.target.value)}
                    />
                  </div>
                )}

                <div style={{ marginBottom: "1.5rem" }}>
                  <div className="text-muted" style={{ fontSize: "0.8rem", marginBottom: "0.5rem" }}>
                    Vista previa de páginas del documento ({selectedDoc.page_count || "?"} páginas):
                  </div>
                  <PagePreview docId={selectedDoc.id} />
                </div>

                <Button variant="primary" size="lg" onClick={handleSplit}>
                  ✂️ Dividir Documento
                </Button>
              </Card>
            ) : (
              <Card>
                <p className="text-muted">Selecciona un documento a la izquierda para configurar la división.</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
