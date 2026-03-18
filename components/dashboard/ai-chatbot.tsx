"use client";

import { useState } from "react";
import { MessageCircle, X, Send, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
}

const initialMessages: Message[] = [
  {
    id: 1,
    role: "assistant",
    content: "안녕하세요! 홈시그널 AI입니다. 부동산 시장 분석, 가격 예측, 투자 전략에 대해 무엇이든 물어보세요.",
  },
];

export function AIChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      role: "user",
      content: input,
    };

    const aiResponse: Message = {
      id: messages.length + 2,
      role: "assistant",
      content: "서울 강남구 아파트 시장은 현재 안정적인 상승세를 보이고 있습니다. AI 분석에 따르면 향후 3개월간 2-3% 상승이 예상됩니다. 더 자세한 분석이 필요하시면 말씀해주세요!",
    };

    setMessages([...messages, userMessage, aiResponse]);
    setInput("");
  };

  return (
    <>
      {/* Floating Button */}
      <Button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 h-14 px-5 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 transition-all z-50 ${
          isOpen ? "scale-0 opacity-0" : "scale-100 opacity-100"
        }`}
        style={{
          boxShadow: "0 0 20px rgba(74, 222, 128, 0.4), 0 4px 12px rgba(0, 0, 0, 0.3)",
        }}
      >
        <Sparkles className="h-5 w-5 mr-2" />
        홈시그널 AI에게 물어보기
      </Button>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          >
            <Card
              className="fixed bottom-6 right-6 w-[380px] h-[500px] bg-card border-border shadow-2xl z-50 flex flex-col overflow-hidden"
              style={{
                boxShadow: "0 0 30px rgba(74, 222, 128, 0.2), 0 10px 40px rgba(0, 0, 0, 0.4)",
              }}
            >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border bg-secondary/50">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <MessageCircle className="h-4 w-4 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">홈시그널 AI</h3>
                <p className="text-xs text-primary">온라인</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setIsOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground rounded-br-md"
                        : "bg-secondary text-foreground rounded-bl-md"
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="메시지를 입력하세요..."
                className="flex-1 h-10 px-4 rounded-full bg-secondary border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
              <Button
                size="icon"
                className="h-10 w-10 rounded-full bg-primary text-primary-foreground"
                onClick={handleSend}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
