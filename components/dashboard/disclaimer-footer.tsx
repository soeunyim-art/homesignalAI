"use client";

import { AlertTriangle } from "lucide-react";

export function DisclaimerFooter() {
  return (
    <footer className="w-full py-4 px-6 border-t border-border bg-background/50">
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <AlertTriangle className="h-3 w-3" />
        <p>
          본 서비스는 통계적 확률 기반 분석으로 투자 결과에 대한 법적 책임을 지지 않습니다.
        </p>
      </div>
    </footer>
  );
}
