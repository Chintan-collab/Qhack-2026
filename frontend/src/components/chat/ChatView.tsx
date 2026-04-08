import { useState } from "react";
import { useParams } from "react-router-dom";
import { MessageSquare, Mic } from "lucide-react";
import clsx from "clsx";
import { useChat } from "../../hooks/useChat";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import VoiceMode from "./VoiceMode";
import AgentBadge from "../agents/AgentBadge";
import PhaseIndicator from "../agents/PhaseIndicator";

export default function ChatView() {
  const { projectId } = useParams<{ projectId: string }>();
  const { messages, isStreaming, activeAgent, currentPhase, sendMessage } = useChat(projectId);
  const [isVoiceMode, setIsVoiceMode] = useState(false);

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

          {/* Voice / Text mode toggle */}
          <div className="flex items-center bg-gray-800 rounded-lg p-0.5">
            <button
              onClick={() => setIsVoiceMode(false)}
              className={clsx(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition",
                !isVoiceMode ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white",
              )}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Text
            </button>
            <button
              onClick={() => setIsVoiceMode(true)}
              className={clsx(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition",
                isVoiceMode ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white",
              )}
            >
              <Mic className="w-3.5 h-3.5" />
              Voice
            </button>
          </div>
        </div>
        {projectId && (
          <div className="mt-3">
            <PhaseIndicator status={displayPhase} />
          </div>
        )}
      </header>

      {isVoiceMode ? (
        <VoiceMode projectId={projectId} />
      ) : (
        <>
          <MessageList messages={messages} isStreaming={isStreaming} />
          <ChatInput onSend={sendMessage} disabled={isStreaming} />
        </>
      )}
    </div>
  );
}
