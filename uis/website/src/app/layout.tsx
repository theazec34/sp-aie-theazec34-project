import type { Metadata, Viewport } from "next";
import { DM_Sans, Playfair_Display } from "next/font/google";
import "./globals.css";

const fontBody = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  display: "swap",
});

const fontDisplay = Playfair_Display({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["700", "900"],
  display: "swap",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  title: "Brasaland — Carta, galería y reservas en Sevilla",
  description:
    "Restaurante Brasaland: carnes a la brasa, arroces y sabor ibérico. Consulta la carta, alérgenos y fotos del proyecto.",
  icons: {
    icon: "/favicon.png",
  },
  openGraph: {
    title: "Brasaland — Carta y reservas",
    description:
      "Carnes a la brasa, arroces y cocina con alma ibérica. Carta digital y galería Brasaland.",
    locale: "es_ES",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={`${fontBody.variable} ${fontDisplay.variable}`}>
      <body>{children}</body>
    </html>
  );
}
