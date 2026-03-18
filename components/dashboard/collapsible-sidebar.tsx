"use client";

import { useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Map,
  TrendingUp,
  FileText,
  Settings,
  HelpCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export type TabType = "overview" | "region" | "price" | "report";

const menuItems: { icon: typeof LayoutDashboard; label: string; tab: TabType | null }[] = [
  { icon: LayoutDashboard, label: "종합 개요", tab: "overview" },
  { icon: Map, label: "지역 분석", tab: "region" },
  { icon: TrendingUp, label: "가격 동향", tab: "price" },
  { icon: FileText, label: "AI 리포트", tab: "report" },
];

const bottomItems = [
  { icon: Settings, label: "설정" },
  { icon: HelpCircle, label: "도움말" },
];

interface CollapsibleSidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export function CollapsibleSidebar({ activeTab, onTabChange }: CollapsibleSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "fixed left-0 top-16 h-[calc(100vh-4rem)] bg-sidebar border-r border-sidebar-border transition-all duration-300 z-40 flex flex-col",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Toggle Button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-3 top-6 h-6 w-6 rounded-full bg-sidebar border border-sidebar-border"
        onClick={() => setCollapsed(!collapsed)}
      >
        {collapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronLeft className="h-3 w-3" />
        )}
      </Button>

      {/* Menu Items */}
      <nav className="p-3 space-y-1 mt-4 flex-1">
        <TooltipProvider delayDuration={0}>
          {menuItems.map((item) => {
            const isActive = item.tab === activeTab;
            return (
              <Tooltip key={item.label}>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full justify-start gap-3 h-10 transition-all duration-200",
                      isActive
                        ? "bg-sidebar-accent text-sidebar-primary"
                        : "text-sidebar-foreground hover:bg-sidebar-accent/50",
                      collapsed && "justify-center px-2"
                    )}
                    onClick={() => item.tab && onTabChange(item.tab)}
                  >
                    <item.icon className={cn("h-5 w-5", isActive && "text-primary")} />
                    {!collapsed && (
                      <span className={cn("text-sm", isActive && "font-medium")}>
                        {item.label}
                      </span>
                    )}
                  </Button>
                </TooltipTrigger>
                {collapsed && (
                  <TooltipContent side="right" className="bg-popover text-popover-foreground">
                    {item.label}
                  </TooltipContent>
                )}
              </Tooltip>
            );
          })}

          <div className="pt-4 border-t border-sidebar-border mt-4">
            {bottomItems.map((item) => (
              <Tooltip key={item.label}>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full justify-start gap-3 h-10 text-sidebar-foreground hover:bg-sidebar-accent/50",
                      collapsed && "justify-center px-2"
                    )}
                  >
                    <item.icon className="h-5 w-5" />
                    {!collapsed && <span className="text-sm">{item.label}</span>}
                  </Button>
                </TooltipTrigger>
                {collapsed && (
                  <TooltipContent side="right" className="bg-popover text-popover-foreground">
                    {item.label}
                  </TooltipContent>
                )}
              </Tooltip>
            ))}
          </div>
        </TooltipProvider>
      </nav>

      {/* Bottom Section */}
      {!collapsed && (
        <div className="p-3">
          <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
            <p className="text-xs text-primary font-medium mb-1">프리미엄 분석</p>
            <p className="text-xs text-muted-foreground">
              AI 심층 분석과 맞춤형 리포트를 이용해보세요
            </p>
            <Button size="sm" className="w-full mt-2 bg-primary text-primary-foreground text-xs">
              업그레이드
            </Button>
          </div>
        </div>
      )}
    </aside>
  );
}
