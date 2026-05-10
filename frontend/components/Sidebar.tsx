"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChartColumnIncreasing,
  CloudUpload,
  PackageSearch,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: ChartColumnIncreasing },
  { href: "/uploads", label: "Uploads", icon: CloudUpload },
  { href: "/products", label: "Products", icon: PackageSearch },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="glass-panel hidden w-72 shrink-0 flex-col rounded-[2rem] border border-border/70 bg-card/82 p-5 lg:flex">
      <Link href="/" className="rounded-[1.5rem] bg-foreground p-5 text-white">
        <p className="text-sm uppercase tracking-[0.3em] text-white/60">Amazon seller</p>
        <p className="mt-3 font-display text-2xl font-semibold">Profit Tracker</p>
        <p className="mt-2 text-sm text-white/70">CSV uploads today, direct report sync next.</p>
      </Link>

      <nav className="mt-6 flex flex-1 flex-col gap-2">
        {links.map((link) => {
          const Icon = link.icon;
          const active = pathname === link.href;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition",
                active
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/10"
                  : "text-muted-foreground hover:bg-white/70 hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="rounded-[1.5rem] border border-dashed border-border bg-white/70 p-4 text-sm text-muted-foreground">
        Update COGS from the Products page whenever sourcing costs change to keep margin accurate.
      </div>
    </aside>
  );
}
