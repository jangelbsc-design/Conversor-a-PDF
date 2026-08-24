"use client";

import React, { useEffect, useState } from "react";
import { api, Document } from "@/lib/api";
import { UploadZone } from "@/components/UploadZone";
import { DocumentCard } from "@/components/DocumentCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { WarningBanner } from "@/components/WarningBanner";
import { SuccessState } from "@/components/states/SuccessState";
import { LoadingState } from "@/components/states/LoadingState";
import { ErrorState } from "@/components/states/ErrorState";

export default function SignPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [signerName, setSignerName] = useState("");
  const [signerEmail, setSignerEmail] = useState("");
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [step, setStep] = useState<"setup" | "consent" | "completed">("setup");
  const [sigRequestId, setSigRequestId] = useState<string | null>(null);
  const [sealedHash, setSealedHash] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.documents.list().then((res) => {
      const docs = res.documents || [];
      setDocuments(docs);
      if (docs.length > 0) setSelectedDoc(docs[0]);
    });
  }, []);

  const handleCreateRequest = async () => {
    if (!selectedDoc || !signerName.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/signatures/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_id: selectedDoc.id,
          signer_name: signerName,
          signer_email_local: signerEmail || "local@local",
          field_positions: [
            {
              page: 1,
              x: 100,
              y: 100,
              width: 200,
              height: 60,
              field_type: "signature",
              label: `Firma: ${signerName}`,
            },
          ],
        }),
      });

      if (!res.ok) {
        let msg = "Error al crear solicitud de firma.";
        try {
          const j = await res.json();
          msg = j.detail || msg;
        } catch {}
        throw new Error(msg);
      }

      const data = await res.json();
      setSigRequestId(data.id);
      setStep("consent");
    } catch (err: any) {
      setError(err.message || "Error al preparar firma");
    } finally {
      setLoading(false);
    }
  };

  const handleRecordConsent = async () => {
    if (!sigRequestId || !consentConfirmed) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/signatures/${sigRequestId}/consent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          signature_request_id: sigRequestId,
          consent_acknowledged: true,
          signer_name_confirmation: signerName,
        }),
      });

      if (!res.ok) {
        let msg = "Error al registrar consentimiento.";
        try {
          const j = await res.json();
          msg = j.detail || msg;
        } catch {}
        throw new Error(msg);
      }

      const sealedData = await res.json();
      setSealedHash(sealedData.final_hash);
      setStep("completed");
    } catch (err: any) {
      setError(err.message || "Error al sellar documento");
    } finally {
      setLoading(false);
    }
  };

  if (step === "completed" && sigRequestId) {
    return (
      <div>
        <h1 className="page-title">Firma Local y Sellado</h1>
        <SuccessState
          title="¡Documento sellado y registrado localmente!"
          description="Se ha registrado el consentimiento con timestamp e IP local (127.0.0.1) y sellado el hash SHA-256 en el log de auditoría."
          downloadUrl={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/signatures/${sigRequestId}/download`}
          downloadFilename="documento_firmado_sellado.pdf"
          sha256={sealedHash}
          onReset={() => {
            setStep("setup");
            setSigRequestId(null);
            setSealedHash(null);
          }}
        />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Firma y Sellado Local</h1>
      <p className="page-subtitle">
        Coloca campos de firma, registra consentimiento local y genera un hash SHA-256 inmutable de sellado.
      </p>

      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      {loading && <LoadingState title="Procesando sellado y registro de auditoría..." />}

      {!loading && !error && step === "setup" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
          <div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              1. Selecciona documento a firmar
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
              2. Datos del firmante
            </h2>

            {selectedDoc ? (
              <Card>
                <div className="input-group" style={{ marginBottom: "1.25rem" }}>
                  <label className="input-label">Nombre completo del firmante:</label>
                  <input
                    className="input"
                    value={signerName}
                    onChange={(e) => setSignerName(e.target.value)}
                    placeholder="Ej: Juan Pérez"
                  />
                </div>

                <div className="input-group" style={{ marginBottom: "1.5rem" }}>
                  <label className="input-label">Correo electrónico (para registro local):</label>
                  <input
                    className="input"
                    value={signerEmail}
                    onChange={(e) => setSignerEmail(e.target.value)}
                    placeholder="juan@ejemplo.local"
                  />
                </div>

                <Button
                  variant="primary"
                  size="lg"
                  disabled={!signerName.trim()}
                  onClick={handleCreateRequest}
                >
                  ✍️ Continuar a Registro de Consentimiento
                </Button>
              </Card>
            ) : (
              <Card>
                <p className="text-muted">Selecciona un documento a la izquierda para iniciar.</p>
              </Card>
            )}
          </div>
        </div>
      )}

      {!loading && !error && step === "consent" && (
        <Card style={{ maxWidth: "600px" }}>
          <h2 style={{ fontSize: "1.2rem", fontWeight: 600, marginBottom: "1rem" }}>
            Declaración de Consentimiento Local
          </h2>

          <div
            style={{
              padding: "1rem",
              background: "var(--bg-elevated)",
              borderRadius: "var(--radius-sm)",
              marginBottom: "1.5rem",
              fontSize: "0.9rem",
              lineHeight: 1.5,
            }}
          >
            Yo, <strong>{signerName}</strong>, confirmo que he revisado el documento y acepto estampar mi firma digital en este archivo.
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={consentConfirmed}
                onChange={(e) => setConsentConfirmed(e.target.checked)}
              />
              <span style={{ fontSize: "0.85rem", fontWeight: 500 }}>
                Confirmar y proceder con la firma del documento
              </span>
            </label>
          </div>

          <div style={{ display: "flex", gap: "1rem" }}>
            <Button
              variant="primary"
              size="lg"
              disabled={!consentConfirmed}
              onClick={handleRecordConsent}
            >
              🔒 Sellar Documento con Hash SHA-256
            </Button>
            <Button variant="secondary" onClick={() => setStep("setup")}>
              Cancelar
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
