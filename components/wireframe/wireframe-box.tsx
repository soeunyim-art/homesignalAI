"use client";

import { cn } from "@/lib/utils";

interface WireframeBoxProps {
  label?: string;
  children?: React.ReactNode;
  className?: string;
  dashed?: boolean;
}

export function WireframeBox({ 
  label, 
  children, 
  className, 
  dashed = false,
  variant = "default" 
}: { 
  label?: string; 
  children?: React.ReactNode; 
  className?: string; 
  dashed?: boolean;
  variant?: "default" | "dashed" | "primary" | "muted";
}) {
  const isDashed = dashed || variant === "dashed";
  const variantStyles = {
    default: "border-border bg-card/50",
    dashed: "border-dashed border-muted-foreground/40 bg-card/30",
    primary: "border-primary/30 bg-primary/5",
    muted: "border-muted-foreground/10 bg-muted/20",
  };

  return (
    <div
      className={cn(
        "border-2 rounded-lg p-4 relative",
        variantStyles[variant] || variantStyles.default,
        isDashed && "border-dashed",
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

export function WireframeDivider({ 
  vertical = false, 
  className 
}: { 
  vertical?: boolean; 
  className?: string; 
}) {
  return (
    <div 
      className={cn(
        "bg-muted-foreground/20 rounded-full",
        vertical ? "w-[1px] h-full mx-2" : "h-[1px] w-full my-2",
        className
      )} 
    />
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
  children,
  className 
}: { 
  size?: "xs" | "sm" | "md" | "lg";
  lines?: number;
  children?: React.ReactNode;
  className?: string;
}) {
  const sizeStyles = {
    xs: "text-[10px] leading-tight",
    sm: "text-xs leading-relaxed",
    md: "text-sm leading-relaxed",
    lg: "text-base leading-relaxed",
  };

  const skeletonSizeStyles = {
    xs: "h-2",
    sm: "h-3",
    md: "h-4",
    lg: "h-6",
  };

  if (children) {
    return <div className={cn(sizeStyles[size], className)}>{children}</div>;
  }

  return (
    <div className={cn("space-y-1", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "bg-muted-foreground/20 rounded",
            skeletonSizeStyles[size],
            i === lines - 1 && lines > 1 ? "w-3/4" : "w-full"
          )}
        />
      ))}
    </div>
  );
}
