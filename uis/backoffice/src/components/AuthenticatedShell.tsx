"use client";

import { ReactNode } from "react";
import AppNav from "./AppNav";
import RequireAuth from "./RequireAuth";

type NavActive = Parameters<typeof AppNav>[0]["active"];

type Props = {
  active?: NavActive;
  children: ReactNode;
};

/** Shared authenticated layout: RequireAuth + sidebar + content shell. */
export default function AuthenticatedShell({ active, children }: Props) {
  return (
    <RequireAuth>
      <main className="bo-shell">
        <AppNav active={active} />
        <section className="bo-content">{children}</section>
      </main>
    </RequireAuth>
  );
}
