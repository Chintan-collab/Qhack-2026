import { useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";
import type { Message } from "../../types/chat";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: Message[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-3">
      {messages.length === 0 && !isStreaming && (
        <div className="flex flex-col items-center justify-center h-full text-center gap-3 opacity-50">
          <p className="text-gray-500 text-sm">Start a conversation with Cleo, your AI Sales Coach</p>
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isStreaming && (
        <div className="flex items-center gap-2 px-4 py-3">
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-gray-800/60 border border-gray-700/40">
            <Loader2 className="w-4 h-4 animate-spin text-[#6565FF]" />
            <span className="text-gray-400 text-sm">Thinking...</span>
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
