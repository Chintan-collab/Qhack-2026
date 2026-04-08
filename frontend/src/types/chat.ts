export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  agentName?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface AgentAction {
  agentName: string;
  action: string;
  input?: Record<string, unknown>;
  output?: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
}

export interface ChatRequest {
  conversationId?: string;
  message: string;
  agentId?: string;
}

export interface ChatResponse {
  conversationId: string;
  message: string;
  agentActions: AgentAction[];
  metadata: Record<string, unknown>;
}

export interface StreamEvent {
  type: "agent_selected" | "message" | "tool_call" | "thinking" | "done" | "error";
  content?: string;
  agent?: string;
  metadata?: Record<string, unknown>;
}
