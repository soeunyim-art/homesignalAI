"use client";

import { cn } from "@/lib/utils";

interface WireframeBoxProps {
  label?: string;
  children?: React.ReactNode;
  className?: string;
  dashed?: boolean;
}

export function WireframeBox({ label, children, className, dashed = false }: WireframeBoxProps) {
  return (
    <div
      className={cn(
        "border-2 rounded-lg p-4 relative",
        dashed ? "border-dashed border-muted-foreground/40" : "border-border",
        "bg-card/50",
        className
      )}
    >
      {label && (
        <span className="absolute -top-3 left-3 bg-background px-2 text-xs text-muted-foreground font-mono">
          {label}
        </span>
      )}
      {children}
    </div>
  );
}

export function WireframePlaceholder({ 
  text, 
  height = "h-8",
  variant = "default" 
}: { 
  text: string; 
  height?: string;
  variant?: "default" | "primary" | "muted";
}) {
  const variantStyles = {
    default: "bg-muted/50 border-muted-foreground/20",
    primary: "bg-primary/10 border-primary/30",
    muted: "bg-muted/30 border-muted-foreground/10",
  };

  return (
    <div className={cn(
      "border rounded flex items-center justify-center text-xs text-muted-foreground font-mono",
      height,
      variantStyles[variant]
    )}>
      {text}
    </div>
  );
}

export function WireframeText({ 
  size = "sm",
  lines = 1,
  className 
}: { 
  size?: "xs" | "sm" | "md" | "lg";
  lines?: number;
  className?: string;
}) {
  const sizeStyles = {
    xs: "h-2",
    sm: "h-3",
    md: "h-4",
    lg: "h-6",
  };

  return (
    <div className={cn("space-y-1", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "bg-muted-foreground/20 rounded",
            sizeStyles[size],
            i === lines - 1 && lines > 1 ? "w-3/4" : "w-full"
          )}
        />
      ))}
    </div>
  );
}

export function WireframeDivider({ className }: { className?: string }) {
  return <div className={cn("w-full h-px bg-muted-foreground/20 my-2", className)} />;
}
