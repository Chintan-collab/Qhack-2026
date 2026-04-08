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
    currentPhase === "deliverable" ||
    currentPhase === "complete" ||
    currentPhase === "strategy" ||
    currentPhase === "financial"
  );

  const phaseStatusMap: Record<string, string> = {
    data_gathering: "gathering",
    research: "researching",
    analysis: "analyzing",
    financial: "financing",
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
    <div className="flex flex-col flex-1 min-h-0 relative" style={{ background: "radial-gradient(circle at top left, rgba(53,53,243,0.08), transparent 40%), radial-gradient(circle at bottom right, rgba(71,71,245,0.06), transparent 40%), linear-gradient(135deg, #07111f 0%, #0b1728 45%, #111827 100%)" }}>
      {/* Header — fixed at top */}
      <header className="sticky top-0 z-10 shrink-0 border-b border-gray-800/60 bg-gray-900/95 backdrop-blur-md px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="w-4 h-4 text-[#6565FF]" />
            <span className="text-sm font-medium text-gray-300">
              {projectId ? "Cleo — Sales Coach" : "Cleo"}
            </span>
            {activeAgent && <AgentBadge agentName={activeAgent} />}
          </div>

          <div className="flex items-center gap-2">
            {canGenerateReport && (
              <button
                onClick={handleGenerateReport}
                disabled={isGeneratingReport}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-[#3535F3] to-[#4747F5] hover:from-[#4747F5] hover:to-[#5555F7] text-white transition-all shadow-lg shadow-[#3535F3]/20 disabled:opacity-50"
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
        <div
          className={clsx(
            "mt-4 mb-1 transition-all duration-500",
            phaseFlash && "scale-[1.02] brightness-125",
          )}
        >
          <PhaseIndicator status={displayPhase} />
        </div>
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
