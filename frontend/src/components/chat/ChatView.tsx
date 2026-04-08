import { useState, useCallback, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { MessageSquare, Mic, FileText, Loader2, Sparkles } from "lucide-react";
import clsx from "clsx";
import { useChat } from "../../hooks/useChat";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import VoiceMode from "./VoiceMode";
import AgentBadge from "../agents/AgentBadge";
import PhaseIndicator from "../agents/PhaseIndicator";

export default function ChatView() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { messages, isStreaming, activeAgent, currentPhase, sendMessage } = useChat(projectId);
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [phaseFlash, setPhaseFlash] = useState(false);
  const prevPhaseRef = useRef(currentPhase);

  // Flash animation when phase changes
  useEffect(() => {
    if (currentPhase && currentPhase !== prevPhaseRef.current) {
      prevPhaseRef.current = currentPhase;
      setPhaseFlash(true);
      const t = setTimeout(() => setPhaseFlash(false), 1200);
      return () => clearTimeout(t);
    }
  }, [currentPhase]);

  const canGenerateReport = projectId && (
    currentPhase === "deliverable" || currentPhase === "complete" || currentPhase === "strategy"
  );

  const phaseStatusMap: Record<string, string> = {
    data_gathering: "gathering",
    research: "researching",
    strategy: "strategizing",
    deliverable: "complete",
    complete: "complete",
  };
  const displayPhase = currentPhase ? (phaseStatusMap[currentPhase] ?? "gathering") : "gathering";

  const handleGenerateReport = useCallback(async () => {
    if (!projectId) return;
    setIsGeneratingReport(true);
    try {
      const res = await fetch(`/api/v1/report/generate/${projectId}`, { method: "POST" });
      const data = await res.json();
      localStorage.setItem("reportData", JSON.stringify(data));
      navigate("/report");
    } catch {
      alert("Failed to generate report.");
    } finally {
      setIsGeneratingReport(false);
    }
  }, [projectId, navigate]);

  return (
    <div className="flex flex-col flex-1 bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800/60 bg-gray-900/80 backdrop-blur-md px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-gray-300">
              {projectId ? "AI Sales Coach" : "Multi-Agent Chat"}
            </span>
            {activeAgent && <AgentBadge agentName={activeAgent} />}
          </div>

          <div className="flex items-center gap-2">
            {canGenerateReport && (
              <button
                onClick={handleGenerateReport}
                disabled={isGeneratingReport}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50"
              >
                {isGeneratingReport ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <FileText className="w-3.5 h-3.5" />
                )}
                {isGeneratingReport ? "Generating..." : "Generate Report"}
              </button>
            )}

            {/* Voice / Text mode toggle */}
            <div className="flex items-center bg-gray-800/80 rounded-xl p-0.5 border border-gray-700/50">
              <button
                onClick={() => setIsVoiceMode(false)}
                className={clsx(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                  !isVoiceMode
                    ? "bg-gray-700 text-white shadow-sm"
                    : "text-gray-400 hover:text-white",
                )}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                Text
              </button>
              <button
                onClick={() => setIsVoiceMode(true)}
                className={clsx(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                  isVoiceMode
                    ? "bg-gray-700 text-white shadow-sm"
                    : "text-gray-400 hover:text-white",
                )}
              >
                <Mic className="w-3.5 h-3.5" />
                Voice
              </button>
            </div>
          </div>
        </div>

        {/* Phase indicator with flash animation */}
        {projectId && (
          <div
            className={clsx(
              "mt-4 mb-1 transition-all duration-500",
              phaseFlash && "scale-[1.02] brightness-125",
            )}
          >
            <PhaseIndicator status={displayPhase} />
          </div>
        )}
      </header>

      {/* Content */}
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
