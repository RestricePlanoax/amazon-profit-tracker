"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BadgeAlert,
  ChartColumnIncreasing,
  CloudUpload,
  PackageSearch,
  ScanSearch,
  Sparkles,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: ChartColumnIncreasing },
  { href: "/alerts", label: "Profit Leaks", icon: BadgeAlert },
  { href: "/briefing", label: "Daily Briefing", icon: Sparkles },
  { href: "/operations", label: "Operations", icon: ScanSearch },
  { href: "/uploads", label: "Uploads", icon: CloudUpload },
  { href: "/products", label: "Products", icon: PackageSearch },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-72 shrink-0 flex-col bg-[var(--nav)] p-4 text-white lg:flex">
      <Link
        href="/"
        className="rounded-[1.35rem] border border-white/10 bg-white/[0.06] p-4 text-white shadow-2xl shadow-black/20"
      >
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[var(--gold)] text-sm font-black text-foreground">
            AP
          </span>
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-white/48">
              Amazon seller
            </p>
            <p className="mt-1 text-lg font-black">Profit Tracker</p>
          </div>
        </div>
        <p className="mt-3 text-xs leading-5 text-white/55">
          CSV uploads, beta sync, and SKU profit decisions.
        </p>
      </Link>

      <nav className="mt-5 flex flex-1 flex-col gap-1">
        {links.map((link) => {
          const Icon = link.icon;
          const active = pathname === link.href;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition",
                active
                  ? "bg-white text-foreground shadow-sm"
                  : "text-white/62 hover:bg-white/[0.08] hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="rounded-[1.35rem] border border-white/10 bg-white/[0.06] p-4 text-xs leading-5 text-white/58">
        <p className="mb-2 font-black text-white">Margin hygiene</p>
        Update COGS from the Products page whenever sourcing costs change to keep margin accurate.
      </div>
    </aside>
  );
}
