import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Permitir imágenes del backend local
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/api/**",
      },
    ],
  },
  // Variables de entorno disponibles en el cliente
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

export default nextConfig;
