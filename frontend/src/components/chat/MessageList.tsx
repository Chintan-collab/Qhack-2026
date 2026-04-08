import type { Message } from "../../types/chat";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: Message[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: Props) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isStreaming && (
        <div className="text-gray-500 text-sm animate-pulse">Agent is thinking...</div>
      )}
    </div>
  );
}
