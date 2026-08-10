import dynamic from "next/dynamic";
import { Header } from "@/components/Header";
import { Hero } from "@/components/Hero";
import { MenuSection } from "@/components/MenuSection";
import { navItems } from "@/data/home";

// Below-the-fold client form — keep out of the critical JS path (LCP / TBT).
const ApplicationForm = dynamic(
  () =>
    import("@/components/ApplicationForm").then((mod) => mod.ApplicationForm),
  {
    loading: () => (
      <section id="aplicar" className="section" aria-busy="true">
        <div className="container">
          <p className="section-text">Cargando formulario…</p>
        </div>
      </section>
    ),
  }
);

// Gallery ships many next/image nodes — defer until after hero + carta.
const GalleryGrid = dynamic(
  () =>
    import("@/components/GalleryGrid").then((mod) => mod.GalleryGrid),
  {
    loading: () => (
      <section id="galeria" className="section section-soft" aria-busy="true">
        <div className="container">
          <p className="section-text">Cargando galería…</p>
        </div>
      </section>
    ),
  }
);

export default function Home() {
  return (
    <>
      <Header navItems={navItems} />
      <main>
        <Hero
          title="El sabor de Sudamerica con alma iberica"
          subtitle="Experiencia Brasaland completa en Next.js: carta total, galeria visual y formulario de aplicacion con validaciones."
        />

        <MenuSection />
        <GalleryGrid />
        <ApplicationForm />
      </main>

      <footer className="site-footer">
        <div className="container">
          <p className="brand">
            Brasa<span className="brand-highlight">land</span>
          </p>
          <p className="footer-text">
            Next.js + TypeScript + React components reutilizables para la web principal.
          </p>
        </div>
      </footer>
    </>
  );
}
