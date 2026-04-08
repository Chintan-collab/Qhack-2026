import { useParams } from "react-router-dom";
import { useChat } from "../../hooks/useChat";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import AgentBadge from "../agents/AgentBadge";
import PhaseIndicator from "../agents/PhaseIndicator";

export default function ChatView() {
  const { projectId } = useParams<{ projectId: string }>();
  const { messages, isStreaming, activeAgent, currentPhase, sendMessage } = useChat(projectId);

  // Map SalesPhase values to project status keys for the indicator
  const phaseStatusMap: Record<string, string> = {
    data_gathering: "gathering",
    research: "researching",
    strategy: "strategizing",
    deliverable: "complete",
    complete: "complete",
  };
  const displayPhase = currentPhase ? (phaseStatusMap[currentPhase] ?? "gathering") : "gathering";

  return (
    <div className="flex flex-col flex-1">
      <header className="border-b border-gray-800 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400">
              {projectId ? "Sales Agent Chat" : "Multi-Agent Chat"}
            </span>
            {activeAgent && <AgentBadge agentName={activeAgent} />}
          </div>
        </div>
        {projectId && (
          <div className="mt-3">
            <PhaseIndicator status={displayPhase} />
          </div>
        )}
      </header>
      <MessageList messages={messages} isStreaming={isStreaming} />
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}
