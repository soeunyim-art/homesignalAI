"use client";

import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Sparkles, Loader2 } from "lucide-react";
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

const suggestedQuestions = [
  "동대문구 아파트 가격 전망은?",
  "최근 뉴스 요약해줘",
  "가장 상승률 높은 동은?",
  "전세가율 분석해줘",
];

// 마크다운 텍스트를 HTML로 간단히 변환하는 헬퍼 함수
const formatMessage = (text: string) => {
  return text
    .split('\n')
    .map((line, idx) => {
      // 헤더 변환
      if (line.startsWith('### ')) {
        return <h3 key={idx} className="text-base font-bold mt-3 mb-1">{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={idx} className="text-lg font-bold mt-4 mb-2">{line.replace('## ', '')}</h2>;
      }
      if (line.startsWith('# ')) {
        return <h1 key={idx} className="text-xl font-bold mt-4 mb-2">{line.replace('# ', '')}</h1>;
      }

      // 리스트 변환
      if (line.trim().startsWith('- ')) {
        return <li key={idx} className="ml-4 my-1">{line.replace(/^-\s*/, '• ')}</li>;
      }
      if (line.match(/^\d+\.\s/)) {
        return <li key={idx} className="ml-4 my-1">{line}</li>;
      }

      // 테이블 행 감지 (간단히)
      if (line.includes('|')) {
        const cells = line.split('|').filter(c => c.trim());
        if (cells.length > 0) {
          return (
            <div key={idx} className="flex gap-2 text-xs border-b border-border/30 py-1">
              {cells.map((cell, i) => (
                <span key={i} className="flex-1">{cell.trim()}</span>
              ))}
            </div>
          );
        }
      }

      // 빈 줄
      if (line.trim() === '') {
        return <br key={idx} />;
      }

      // 일반 텍스트
      return <p key={idx} className="my-1">{line}</p>;
    });
};

export function AIChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // 메시지 추가 시 자동 스크롤
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: messages.length + 1,
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage].map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "응답 생성에 실패했습니다.");
      }

      const data = await response.json();

      const aiMessage: Message = {
        id: messages.length + 2,
        role: "assistant",
        content: data.message,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error: any) {
      console.error("Chat error:", error);
      setError(error.message);

      // 에러 메시지를 챗봇 응답으로 추가
      const errorMessage: Message = {
        id: messages.length + 2,
        role: "assistant",
        content: `죄송합니다. 오류가 발생했습니다: ${error.message}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  return (
    <>
      {/* Floating Button */}
      <motion.div
        initial={{ opacity: 1, scale: 1 }}
        animate={{
          opacity: isOpen ? 0 : 1,
          scale: isOpen ? 0 : 1,
        }}
        transition={{ duration: 0.2 }}
        className="fixed bottom-6 right-6 z-40"
        style={{ pointerEvents: isOpen ? 'none' : 'auto' }}
      >
        <Button
          onClick={() => setIsOpen(true)}
          className="h-14 px-5 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 transition-all"
          style={{
            boxShadow: "0 0 20px rgba(74, 222, 128, 0.4), 0 4px 12px rgba(0, 0, 0, 0.3)",
          }}
        >
          <Sparkles className="h-5 w-5 mr-2" />
          홈시그널 AI에게 물어보기
        </Button>
      </motion.div>

      {/* Chat Sidebar */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Sidebar */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed top-0 right-0 h-full w-[500px] z-50"
            >
              <Card
                className="h-full bg-card border-l border-border shadow-2xl flex flex-col overflow-hidden"
                style={{
                  boxShadow: "-10px 0 40px rgba(0, 0, 0, 0.3)",
                }}
              >
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-border bg-gradient-to-r from-primary/10 to-primary/5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                      <Sparkles className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-foreground">홈시그널 AI</h3>
                      <p className="text-xs text-primary flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                        온라인
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9 hover:bg-secondary"
                    onClick={() => setIsOpen(false)}
                  >
                    <X className="h-5 w-5" />
                  </Button>
                </div>

                {/* Messages */}
                <ScrollArea className="flex-1 p-6" ref={scrollAreaRef}>
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl px-5 py-3 ${
                            message.role === "user"
                              ? "bg-primary text-primary-foreground rounded-br-md"
                              : "bg-secondary text-foreground rounded-bl-md border border-border/50"
                          }`}
                        >
                          <div className="text-sm leading-relaxed">
                            {message.role === "assistant" ? (
                              <div className="space-y-1">{formatMessage(message.content)}</div>
                            ) : (
                              <p className="whitespace-pre-wrap">{message.content}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* 로딩 상태 */}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-secondary rounded-2xl px-5 py-3 rounded-bl-md border border-border/50">
                          <div className="flex items-center gap-2">
                            <Loader2 className="h-4 w-4 animate-spin text-primary" />
                            <span className="text-sm text-muted-foreground">생각 중...</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 제안 질문 (메시지가 1개일 때만 표시) */}
                    {messages.length === 1 && !isLoading && (
                      <div className="space-y-3 mt-6">
                        <p className="text-xs text-muted-foreground font-medium px-1">💡 추천 질문</p>
                        <div className="grid grid-cols-2 gap-3">
                          {suggestedQuestions.map((question, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSuggestedQuestion(question)}
                              className="text-sm bg-secondary/70 hover:bg-secondary border border-border rounded-xl px-4 py-3 text-left transition-all hover:shadow-md hover:scale-[1.02]"
                            >
                              {question}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </ScrollArea>

                {/* Input */}
                <div className="p-6 border-t border-border bg-secondary/30">
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && !isLoading && handleSend()}
                      placeholder="메시지를 입력하세요... (Shift+Enter로 줄바꿈)"
                      disabled={isLoading}
                      className="flex-1 h-11 px-4 rounded-xl bg-background border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    />
                    <Button
                      size="icon"
                      className="h-11 w-11 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all"
                      onClick={handleSend}
                      disabled={isLoading || !input.trim()}
                    >
                      {isLoading ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                      ) : (
                        <Send className="h-5 w-5" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2 text-center">
                    AI가 생성한 답변은 참고용이며, 투자 결정은 신중히 하시기 바랍니다.
                  </p>
                </div>
              </Card>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
