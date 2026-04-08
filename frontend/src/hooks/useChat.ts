import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import { api } from "../services/api";
import { createChatSocket } from "../services/websocket";
import type { Message, StreamEvent } from "../types/chat";

export function useChat(projectId?: string) {
  const store = useChatStore();
  const wsRef = useRef<WebSocket | null>(null);
  const initializedRef = useRef(false);

  // On mount: if we have a projectId, load project phase + existing conversation
  useEffect(() => {
    if (!projectId || initializedRef.current) return;
    initializedRef.current = true;

    // Clear previous chat state but keep phase until loaded
    store.clearMessages();
    store.setActiveConversation(null);

    // Load project phase immediately
    api.projects.get(projectId).then((project) => {
      store.setCurrentPhase(project.status ?? "data_gathering");
    }).catch(() => {
      store.setCurrentPhase("data_gathering");
    });

    // Resume existing conversation and load messages
    api.projects.getConversation(projectId).then(async (convId) => {
      if (convId) {
        store.setActiveConversation(convId);
        // Load existing messages from DB
        try {
          const conv = await api.conversations.get(convId);
          const messages: Message[] = (conv as any).messages?.map((m: any) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            agentName: m.agent_name,
            timestamp: m.created_at || new Date().toISOString(),
          })) || [];
          for (const msg of messages) {
            store.addMessage(msg);
          }
        } catch {
          // No messages yet — fresh conversation
        }
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
        conversation_id: store.activeConversationId ?? undefined,
        project_id: projectId ?? undefined,
        message: content,
      });

      // Store the conversation ID for subsequent messages
      if (!store.activeConversationId) {
        store.setActiveConversation(response.conversation_id);
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
