"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Header } from "@/components/dashboard/header";
import { HomeSearch } from "@/components/dashboard/home-search";
import { CollapsibleSidebar, type TabType } from "@/components/dashboard/collapsible-sidebar";
import { Overview } from "@/components/dashboard/tabs/overview";
import { RegionAnalysis } from "@/components/dashboard/tabs/region-analysis";
import { PriceTrends } from "@/components/dashboard/tabs/price-trends";
import { AIReport } from "@/components/dashboard/tabs/ai-report";
import { AIChatbot } from "@/components/dashboard/ai-chatbot";
import { DisclaimerFooter } from "@/components/dashboard/disclaimer-footer";

type PageType = "home" | "dashboard";

export default function DashboardPage() {
  const [page, setPage] = useState<PageType>("home");
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setPage("dashboard");
    setActiveTab("overview");
  };

  const handleLogoClick = () => {
    setPage("home");
    setSearchQuery("");
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "overview":
        return <Overview searchQuery={searchQuery} />;
      case "region":
        return <RegionAnalysis searchQuery={searchQuery} />;
      case "price":
        return <PriceTrends searchQuery={searchQuery} />;
      case "report":
        return <AIReport searchQuery={searchQuery} />;
      default:
        return <Overview searchQuery={searchQuery} />;
    }
  };

  return (
    <div className="min-h-screen bg-background relative">
      {/* Dot Grid Background Pattern */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <svg className="w-full h-full opacity-[0.03]">
          <defs>
            <pattern
              id="bgDotGrid"
              x="0"
              y="0"
              width="24"
              height="24"
              patternUnits="userSpaceOnUse"
            >
              <circle cx="2" cy="2" r="1" fill="#4ADE80" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#bgDotGrid)" />
        </svg>
      </div>

      <AnimatePresence mode="wait">
        {page === "home" ? (
          <motion.div
            key="home"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <HomeSearch onSearch={handleSearch} />
          </motion.div>
        ) : (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Header with back to home */}
            <Header onLogoClick={handleLogoClick} searchQuery={searchQuery} onSearch={handleSearch} />

            {/* Sidebar */}
            <CollapsibleSidebar activeTab={activeTab} onTabChange={setActiveTab} />

            {/* Main Content */}
            <main className="pl-16 lg:pl-56 transition-all duration-300">
              <div className="p-4 lg:p-6">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    {renderTabContent()}
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* Footer */}
              <DisclaimerFooter />
            </main>

            {/* Floating AI Chatbot */}
            <AIChatbot />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
