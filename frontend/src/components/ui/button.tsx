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
          "inline-flex items-center justify-center font-medium transition-all duration-200",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          {
            "bg-accent text-white hover:bg-accent-hover active:scale-[0.98]":
              variant === "primary",
            "bg-surface-elevated text-text border border-border hover:border-text-muted":
              variant === "secondary",
            "text-text-secondary hover:text-text hover:bg-surface-elevated":
              variant === "ghost",
          },
          {
            "h-8 px-3 text-sm rounded-lg": size === "sm",
            "h-10 px-4 text-sm rounded-lg": size === "md",
            "h-12 px-6 text-base rounded-xl": size === "lg",
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
