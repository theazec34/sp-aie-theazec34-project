import { ApplicationForm } from "@/components/ApplicationForm";
import { GalleryGrid } from "@/components/GalleryGrid";
import { Header } from "@/components/Header";
import { Hero } from "@/components/Hero";
import { MenuSection } from "@/components/MenuSection";
import { navItems } from "@/data/home";

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
          <p className="footer-text">Next.js + TypeScript + React components reutilizables para la web principal.</p>
        </div>
      </footer>
    </>
  );
}
