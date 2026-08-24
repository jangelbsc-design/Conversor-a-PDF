import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "PDF Suite Local | Reemplazo Personal de ILovePDF",
  description: "Suite PDF privada y local sin subida a servidores externos ni telemetría.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        <div className="app-layout">
          <Sidebar />
          <main className="app-main">
            <div className="app-content">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
