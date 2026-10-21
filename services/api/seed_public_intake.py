"""Seed demo reservations + career applications (idempotent by email)."""

from __future__ import annotations

import sys
from datetime import date, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.public_intake.models import CareerCreate, ReservationCreate  # noqa: E402
from app.public_intake.repository import PublicIntakeRepository  # noqa: E402


def main() -> int:
    repo = PublicIntakeRepository()
    try:
        # Repair empty / corrupt TinyDB file
        if repo.db_path.exists() and repo.db_path.stat().st_size == 0:
            repo.db_path.write_text("{}\n", encoding="utf-8")
            repo.close()
            repo = PublicIntakeRepository()

        existing_res = {r.email.lower() for r in repo.list_reservations()}
        existing_car = {c.email.lower() for c in repo.list_careers()}

        demo_day = date.today() + timedelta(days=14)
        res_email = "maria.lopez.demo@example.com"
        if res_email not in existing_res:
            repo.create_reservation(
                ReservationCreate(
                    full_name="María López Demo",
                    phone="+34 612 345 678",
                    email=res_email,
                    date=demo_day,
                    time=time(21, 0),
                    guests=4,
                    notes="Mesa cerca de la parrilla si es posible. Cumpleaños.",
                )
            )
            print(f"  reservation ...... {res_email}")
        else:
            print(f"  reservation skip . {res_email}")

        car_email = "luis.herrera.demo@example.com"
        if car_email not in existing_car:
            repo.create_career(
                CareerCreate(
                    name="Luis Herrera Demo",
                    email=car_email,
                    phone="+34 600 111 222",
                    department="Sala",
                    experience_years=3,
                    message=(
                        "Experiencia en sala de asador; disponible turnos noche "
                        "y fines de semana."
                    ),
                    cv_filename="cv-luis-herrera-demo.pdf",
                    privacy_accepted=True,
                )
            )
            print(f"  career ........... {car_email}")
        else:
            print(f"  career skip ...... {car_email}")

        print("OK — public intake sembrado.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR — seed_public_intake: {exc}", file=sys.stderr)
        return 1
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit(main())
