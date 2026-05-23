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
        <div className="polaris-card px-8 py-6 text-center">
          <p className="font-display text-2xl font-semibold">Checking your session</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Redirecting if you need to sign in first.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen w-full max-w-[1540px] gap-0">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col lg:rounded-l-[2rem] lg:bg-background">
          <Navbar title={title} onLogout={handleLogout} />
          <main className="flex-1 px-4 py-5 lg:px-8 lg:py-7">{children}</main>
        </div>
      </div>
    </div>
  );
}
