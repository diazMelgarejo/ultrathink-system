import type { ReactNode } from "react";
import { EnvBar } from "./EnvBar";
import { NavLeft } from "./NavLeft";
import type { AppState } from "@/api/appState";

interface ShellProps {
  state: AppState | undefined;
  isFetching?: boolean;
  children: ReactNode;
  activePage?: string;
  onNavigate?: (page: string) => void;
}

export function Shell({ state, isFetching, children, activePage, onNavigate }: ShellProps) {
  return (
    <div className="flex h-screen flex-col bg-canvas">
      <EnvBar state={state} isFetching={isFetching} />
      <div className="flex flex-1 overflow-hidden">
        <NavLeft active={activePage} onSelect={onNavigate} />
        <main className="flex-1 overflow-auto px-4 py-4">{children}</main>
      </div>
    </div>
  );
}
