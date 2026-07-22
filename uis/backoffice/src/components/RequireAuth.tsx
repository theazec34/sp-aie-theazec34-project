"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "../lib/auth";

type Props = {
  children: React.ReactNode;
};

/** Client-side guard: redirects to /login when there is no JWT in localStorage. */
export default function RequireAuth({ children }: Props) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <main className="auth-shell">
        <p className="bo-soft">Comprobando sesión…</p>
      </main>
    );
  }

  return <>{children}</>;
}
