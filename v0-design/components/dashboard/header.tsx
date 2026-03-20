"use client";

import { useState } from "react";
import { Search, ChevronDown, Bell, User, Home } from "lucide-react";
import { HomeSignalLogo } from "./logo";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const regions = [
  "서울특별시",
  "경기도",
  "인천광역시",
  "부산광역시",
  "대구광역시",
  "대전광역시",
  "광주광역시",
  "울산광역시",
  "세종특별자치시",
];

interface HeaderProps {
  onLogoClick?: () => void;
  searchQuery?: string;
  onSearch?: (query: string) => void;
}

export function Header({ onLogoClick, searchQuery, onSearch }: HeaderProps) {
  const [localQuery, setLocalQuery] = useState(searchQuery || "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (localQuery.trim() && onSearch) {
      onSearch(localQuery);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-4 lg:px-6">
        {/* Logo */}
        <div 
          className="cursor-pointer flex items-center gap-2" 
          onClick={onLogoClick}
        >
          <HomeSignalLogo />
          {onLogoClick && (
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              <Home className="h-4 w-4 mr-1" />
              홈으로
            </Button>
          )}
        </div>

        {/* Center Search + Region */}
        <div className="hidden md:flex items-center gap-3 flex-1 max-w-2xl mx-8">
          {/* Current Search Query Badge */}
          {searchQuery && (
            <Badge variant="outline" className="border-primary text-primary px-3 py-1">
              {searchQuery}
            </Badge>
          )}

          {/* Search Bar */}
          <form onSubmit={handleSubmit} className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="분석할 지역 또는 아파트명을 입력하세요"
              value={localQuery}
              onChange={(e) => setLocalQuery(e.target.value)}
              className="w-full h-10 pl-10 pr-4 rounded-lg bg-secondary border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
            />
          </form>

          {/* Region Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="min-w-[140px] justify-between bg-secondary border-border">
                서울특별시
                <ChevronDown className="h-4 w-4 ml-2 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[160px]">
              {regions.map((region) => (
                <DropdownMenuItem key={region}>{region}</DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-primary" />
          </Button>
          <Button variant="ghost" size="icon" className="rounded-full bg-secondary">
            <User className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}
