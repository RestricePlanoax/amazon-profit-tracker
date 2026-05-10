"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { Sidebar } from "@/components/Sidebar";
import { clearToken, getToken } from "@/lib/auth";

type AppShellProps = {
  children: React.ReactNode;
  title: string;
};

export function AppShell({ children, title }: AppShellProps) {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
    }
  }, [router]);

  const handleLogout = () => {
    clearToken();
    router.push("/");
  };

  if (!getToken()) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <div className="glass-panel rounded-[2rem] border border-border/70 bg-card/85 px-8 py-6 text-center">
          <p className="font-display text-2xl font-semibold">Checking your session</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Redirecting if you need to sign in first.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-4 lg:px-6">
      <div className="mx-auto flex min-h-[calc(100vh-2rem)] w-full max-w-7xl gap-4">
        <Sidebar />
        <div className="flex flex-1 flex-col gap-4">
          <Navbar title={title} onLogout={handleLogout} />
          <main className="flex-1">{children}</main>
        </div>
      </div>
    </div>
  );
}
