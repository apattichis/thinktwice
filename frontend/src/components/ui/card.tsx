"use client";

import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "glass";
}

export function Card({ className, variant = "default", children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border transition-all duration-200",
        {
          "bg-bg-secondary border-border-default shadow-sm":
            variant === "default",
          "bg-bg-secondary border-border-default shadow-md shadow-black/[0.04]":
            variant === "elevated",
          "glass border-border-default shadow-sm":
            variant === "glass",
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-5 py-4 border-b border-border-subtle", className)} {...props}>
      {children}
    </div>
  );
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-5 py-4", className)} {...props}>
      {children}
    </div>
  );
}
