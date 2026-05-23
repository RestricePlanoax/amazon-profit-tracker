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
    <header className="sticky top-0 z-20 border-b border-border/70 bg-background/82 px-4 py-4 backdrop-blur-xl lg:px-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-primary">
            Workspace
          </p>
          <h1 className="font-display text-3xl font-black">{title}</h1>
        </div>

        <Button variant="outline" onClick={onLogout}>
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>

      <div className="mt-3 rounded-3xl border border-border bg-card p-3 shadow-sm lg:hidden">
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
                "rounded-lg px-3 py-2 text-sm font-semibold transition",
                pathname === link.href
                  ? "bg-primary text-primary-foreground"
                  : "bg-card text-foreground hover:bg-muted",
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
