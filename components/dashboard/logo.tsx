"use client";

export function HomeSignalLogo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg
        width="32"
        height="32"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
      >
        {/* 3x3 Mint Dot Grid */}
        <circle cx="8" cy="8" r="3" fill="#4ADE80" />
        <circle cx="16" cy="8" r="3" fill="#4ADE80" />
        <circle cx="24" cy="8" r="3" fill="#4ADE80" />
        <circle cx="8" cy="16" r="3" fill="#4ADE80" />
        <circle cx="16" cy="16" r="3" fill="#4ADE80" />
        <circle cx="24" cy="16" r="3" fill="#4ADE80" />
        <circle cx="8" cy="24" r="3" fill="#4ADE80" />
        <circle cx="16" cy="24" r="3" fill="#4ADE80" />
        <circle cx="24" cy="24" r="3" fill="#4ADE80" />
      </svg>
      <span className="text-xl font-bold text-foreground">
        홈시그널<span className="text-primary">AI</span>
      </span>
    </div>
  );
}
