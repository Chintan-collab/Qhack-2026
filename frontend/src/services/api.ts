import type { ChatRequest, ChatResponse, Conversation } from "../types/chat";
import type { AgentInfo } from "../types/agent";

const BASE_URL = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  chat: {
    send: (data: ChatRequest) =>
      request<ChatResponse>("/chat/", { method: "POST", body: JSON.stringify(data) }),
  },

  conversations: {
    list: () => request<Conversation[]>("/conversations/"),
    get: (id: string) => request<Conversation>(`/conversations/${id}`),
    delete: (id: string) =>
      request<{ deleted: boolean }>(`/conversations/${id}`, { method: "DELETE" }),
  },

  agents: {
    list: () => request<AgentInfo[]>("/agents/"),
    get: (id: string) => request<AgentInfo>(`/agents/${id}`),
  },
};
