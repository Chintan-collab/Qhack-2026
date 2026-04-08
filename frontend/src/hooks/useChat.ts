import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import { api } from "../services/api";
import { createChatSocket } from "../services/websocket";
import type { Message, StreamEvent } from "../types/chat";

export function useChat(projectId?: string) {
  const store = useChatStore();
  const wsRef = useRef<WebSocket | null>(null);
  const initializedRef = useRef(false);

  // On mount: if we have a projectId, look up existing conversation
  useEffect(() => {
    if (!projectId || initializedRef.current) return;
    initializedRef.current = true;

    api.projects.getConversation(projectId).then((convId) => {
      if (convId) {
        store.setActiveConversation(convId);
      }
    });
  }, [projectId, store]);

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
        projectId: projectId ?? undefined,
        message: content,
      });

      // Store the conversation ID for subsequent messages
      if (!store.activeConversationId) {
        store.setActiveConversation(response.conversationId);
      }

      // Track phase changes
      const phase = response.metadata?.phase as string | undefined;
      if (phase) {
        store.setCurrentPhase(phase);
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.message,
        agentName: response.metadata?.agent_name as string | undefined,
        timestamp: new Date().toISOString(),
        metadata: response.metadata,
      };
      store.addMessage(assistantMessage);
    },
    [store, projectId],
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
            case "phase_changed":
              store.setCurrentPhase(event.phase ?? null);
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
    currentPhase: store.currentPhase,
    sendMessage,
    startStreaming,
    stopStreaming,
  };
}
