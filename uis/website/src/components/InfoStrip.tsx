import { hours, restaurant, specialty } from "@/data/site";

export function InfoStrip() {
  return (
    <section className="info-strip" aria-label="Información práctica">
      <div className="container info-strip-grid">
        <div>
          <p className="info-label">Ubicación</p>
          <p className="info-value">{restaurant.address}</p>
        </div>
        <div>
          <p className="info-label">Horario</p>
          <p className="info-value">
            {hours.lines[0]}
            {hours.provisional ? (
              <span className="info-provisional"> · orientativo</span>
            ) : null}
          </p>
        </div>
        <div>
          <p className="info-label">Especialidad</p>
          <p className="info-value">{specialty}</p>
        </div>
      </div>
    </section>
  );
}
