import { useCallback, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import { api } from "../services/api";
import { createChatSocket } from "../services/websocket";
import type { Message, StreamEvent } from "../types/chat";

export function useChat() {
  const store = useChatStore();
  const wsRef = useRef<WebSocket | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };
      store.addMessage(userMessage);

      const response = await api.chat.send({
        conversationId: store.activeConversationId ?? undefined,
        message: content,
      });

      if (!store.activeConversationId) {
        store.setActiveConversation(response.conversationId);
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.message,
        timestamp: new Date().toISOString(),
        metadata: response.metadata,
      };
      store.addMessage(assistantMessage);
    },
    [store],
  );

  const startStreaming = useCallback(
    (conversationId: string) => {
      store.setIsStreaming(true);

      const ws = createChatSocket(
        conversationId,
        (event: StreamEvent) => {
          switch (event.type) {
            case "agent_selected":
              store.setActiveAgent(event.agent ?? null);
              break;
            case "message":
              store.appendToLastMessage(event.content ?? "");
              break;
            case "done":
              store.setIsStreaming(false);
              store.setActiveAgent(null);
              break;
            case "error":
              store.setIsStreaming(false);
              break;
          }
        },
        () => store.setIsStreaming(false),
      );

      wsRef.current = ws;
    },
    [store],
  );

  const stopStreaming = useCallback(() => {
    wsRef.current?.close();
    store.setIsStreaming(false);
  }, [store]);

  return {
    messages: store.messages,
    isStreaming: store.isStreaming,
    activeAgent: store.activeAgent,
    sendMessage,
    startStreaming,
    stopStreaming,
  };
}
