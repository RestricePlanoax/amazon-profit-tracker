import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "default" | "outline" | "ghost";
type ButtonSize = "default" | "icon";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const variantClasses: Record<ButtonVariant, string> = {
  default:
    "border border-primary bg-primary text-primary-foreground shadow-sm shadow-emerald-950/10 hover:-translate-y-0.5 hover:bg-[#066656] disabled:border-[#95c9bc] disabled:bg-[#95c9bc]",
  outline:
    "border border-border bg-card text-foreground shadow-sm hover:-translate-y-0.5 hover:bg-[var(--surface-subdued)] disabled:text-muted-foreground",
  ghost: "bg-transparent text-foreground hover:bg-muted",
};

const sizeClasses: Record<ButtonSize, string> = {
  default: "h-11 px-5 py-2.5",
  icon: "h-11 w-11 p-0 justify-center",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", type = "button", ...props }, ref) => {
    return (
      <button
        ref={ref}
        type={type}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-2xl text-sm font-black transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)] disabled:cursor-not-allowed disabled:hover:translate-y-0",
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
