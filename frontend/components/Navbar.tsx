"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MenuSquare, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type NavbarProps = {
  title: string;
  onLogout: () => void;
};

export function Navbar({ title, onLogout }: NavbarProps) {
  const pathname = usePathname();
  const mobileLinks = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/uploads", label: "Uploads" },
    { href: "/products", label: "Products" },
    { href: "/settings", label: "Settings" },
  ];

  return (
    <header className="glass-panel rounded-[1.75rem] border border-border/70 bg-card/82 px-5 py-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-muted-foreground">Workspace</p>
          <h1 className="font-display text-3xl font-semibold">{title}</h1>
        </div>

        <Button variant="outline" onClick={onLogout}>
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>

      <div className="mt-4 rounded-2xl border border-dashed border-border bg-white/55 p-3 lg:hidden">
        <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
          <MenuSquare className="h-4 w-4 text-primary" />
          Quick navigation
        </div>
        <div className="flex flex-wrap gap-2">
          {mobileLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-full px-3 py-2 text-sm font-semibold transition",
                pathname === link.href
                  ? "bg-primary text-primary-foreground"
                  : "bg-white text-foreground hover:bg-accent",
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}
