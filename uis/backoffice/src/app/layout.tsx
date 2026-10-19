import type { Metadata, Viewport } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import TelemetryProvider from "../components/TelemetryProvider";
import WebVitalsReporter from "../components/WebVitalsReporter";
import "./globals.css";

const bodyFont = IBM_Plex_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "600"],
  display: "swap",
});

const displayFont = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["700"],
  display: "swap",
});

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
    <html lang="es" className={`${bodyFont.variable} ${displayFont.variable}`}>
      <body>
        <TelemetryProvider>
          <WebVitalsReporter />
          {children}
        </TelemetryProvider>
      </body>
    </html>
  );
}
