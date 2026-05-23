"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { getToken, setToken } from "@/lib/auth";

type AuthFormProps = {
  mode: "login" | "signup";
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (getToken()) {
      router.replace("/dashboard");
    }
  }, [router]);

  const isSignup = mode === "signup";

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = isSignup
        ? await api.signup({ email, password })
        : await api.login({ email, password });
      setToken(response.access_token);
      if (isSignup) {
        router.push("/onboarding");
        return;
      }

      const me = await api.getMe();
      router.push(me.needs_onboarding ? "/onboarding" : "/dashboard");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-10">
      <div className="grid w-full max-w-6xl gap-8 lg:grid-cols-[1fr_0.9fr]">
        <section className="polaris-card p-8 lg:p-10">
          <div className="max-w-xl">
            <p className="text-sm font-semibold text-primary">
              Amazon Seller Profit Tracker
            </p>
            <h1 className="mt-4 font-display text-5xl font-semibold leading-tight">
              {isSignup
                ? "Start tracking real Amazon profit in minutes"
                : "Welcome back to your profit dashboard"}
            </h1>
            <p className="mt-4 text-lg leading-8 text-muted-foreground">
              {isSignup
                ? "Create your account, upload order and ad reports, and turn raw CSV files into clear daily profit visibility."
                : "Sign in to review profitability by day and by SKU, then update COGS as your inventory costs change."}
            </p>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            {[
              "Auto-created store for MVP onboarding",
              "CSV upload with background processing",
              "Dashboard plus SKU profitability",
            ].map((item) => (
              <div key={item} className="rounded-lg border border-border bg-card p-4 text-sm">
                {item}
              </div>
            ))}
          </div>
        </section>

        <section className="polaris-card p-8 lg:p-10">
          <div>
            <p className="text-xs font-semibold uppercase text-muted-foreground">
              {isSignup ? "Create account" : "Login"}
            </p>
            <h2 className="mt-3 font-display text-3xl font-semibold">
              {isSignup ? "Set up your MVP account" : "Sign in with email and password"}
            </h2>
          </div>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-semibold text-foreground">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="seller@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-semibold text-foreground">
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength={8}
                required
              />
            </div>

            {error ? (
              <div className="rounded-lg border border-danger/20 bg-danger/8 px-4 py-3 text-sm text-danger">
                {error}
              </div>
            ) : null}

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Please wait..." : isSignup ? "Create account" : "Login"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground">
            {isSignup ? "Already have an account?" : "Need an account?"}{" "}
            <Link
              href={isSignup ? "/login" : "/signup"}
              className="font-semibold text-primary transition hover:text-primary/80"
            >
              {isSignup ? "Login" : "Sign up"}
            </Link>
          </p>
        </section>
      </div>
    </main>
  );
}
