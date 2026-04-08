import { useChat } from "../../hooks/useChat";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";

export default function ChatView() {
  const { messages, isStreaming, activeAgent, sendMessage } = useChat();

  return (
    <div className="flex flex-col flex-1">
      <header className="border-b border-gray-800 px-6 py-3 text-sm text-gray-400">
        {activeAgent ? `Agent: ${activeAgent}` : "Multi-Agent Chat"}
      </header>
      <MessageList messages={messages} isStreaming={isStreaming} />
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}
