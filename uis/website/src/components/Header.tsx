import Image from "next/image";
import { NavItem } from "@/types/site";

interface HeaderProps {
  navItems: NavItem[];
}

export function Header({ navItems }: HeaderProps) {
  return (
    <header className="site-header">
      <div className="container site-header-inner">
        <a href="#inicio" className="brand" aria-label="Brasaland inicio">
          <Image
            className="brand-mark"
            src="/Imagenes/Icono principal.png"
            alt="Icono Brasaland"
            width={44}
            height={44}
          />
          <span>
            Brasa<span className="brand-highlight">land</span>
          </span>
        </a>
        <nav className="nav-links" aria-label="Navegacion principal">
          {navItems.map((item) => (
            <a key={item.id} href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
