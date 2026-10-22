import type { Metadata, Viewport } from "next";
import TelemetryProvider from "../components/TelemetryProvider";
import WebVitalsReporter from "../components/WebVitalsReporter";
import "./globals.css";

/**
 * Sin next/font/google: en Docker/Codespaces sin salida a fonts.googleapis.com
 * cada compilación reintentaba y dejaba el login colgado en «Entrando…».
 * Las variables se definen en globals.css con stacks locales.
 */

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  title: "Brasaland — Panel interno",
  description:
    "Panel interno Brasaland: proveedores, incidencias, inventario, conocimiento y RFP.",
  icons: {
    icon: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // Extensiones del navegador inyectan attrs (bis_skin_checked) → mismatch DEV
    <html lang="es" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <TelemetryProvider>
          <WebVitalsReporter />
          {children}
        </TelemetryProvider>
      </body>
    </html>
  );
}
