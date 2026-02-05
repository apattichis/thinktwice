"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-all duration-200 rounded-lg",
          "disabled:opacity-40 disabled:cursor-not-allowed",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 focus-visible:ring-offset-2",
          "active:scale-[0.97]",
          {
            "bg-brand text-white shadow-sm shadow-brand/20 hover:bg-brand-dark":
              variant === "primary",
            "bg-bg-secondary text-text-primary border border-border-strong hover:bg-bg-hover":
              variant === "secondary",
            "text-text-secondary hover:text-text-primary hover:bg-bg-hover":
              variant === "ghost",
          },
          {
            "h-8 px-3 text-[13px] rounded-md gap-1.5": size === "sm",
            "h-9 px-4 text-sm gap-2": size === "md",
            "h-11 px-5 text-[15px] gap-2.5 rounded-xl": size === "lg",
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
