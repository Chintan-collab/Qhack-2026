import { Volume2 } from "lucide-react";
import clsx from "clsx";
import { useVoiceChat } from "../../hooks/useVoiceChat";
import AgentBadge from "../agents/AgentBadge";

interface Props {
  projectId?: string;
}

export default function VoiceMode({ projectId }: Props) {
  const {
    isRecording,
    isProcessing,
    isSpeaking,
    isLoopActive,
    error,
    startLoop,
    stopLoop,
    messages,
    activeAgent,
  } = useVoiceChat(projectId);

  const lastAssistantMsg = [...messages]
    .reverse()
    .find((m) => m.role === "assistant");
  const lastUserMsg = [...messages]
    .reverse()
    .find((m) => m.role === "user");

  const handleMainClick = () => {
    if (isLoopActive) {
      stopLoop();
    } else {
      startLoop();
    }
  };

  let statusText = "Tap to start conversation";
  if (isRecording) statusText = "Listening...";
  if (isProcessing) statusText = "Thinking...";
  if (isSpeaking) statusText = "Speaking...";
  if (error) statusText = error;

  // Determine orb state for CSS class
  const orbState = isRecording
    ? "recording"
    : isProcessing
      ? "processing"
      : isSpeaking
        ? "speaking"
        : isLoopActive
          ? "idle-active"
          : "idle";

  return (
    <div className="flex flex-col items-center justify-center flex-1 px-8 relative overflow-hidden">
      {/* Background ambient glow */}
      <div
        className={clsx(
          "absolute inset-0 transition-opacity duration-1000",
          (isRecording || isSpeaking || isProcessing) ? "opacity-100" : "opacity-0",
        )}
      >
        <div className={clsx(
          "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full blur-[120px] transition-all duration-1000",
          isRecording && "w-96 h-96 bg-red-500/20",
          isProcessing && "w-80 h-80 bg-[#4747F5]/15",
          isSpeaking && "w-96 h-96 bg-[#5555F7]/20",
        )} />
      </div>

      {activeAgent && (
        <div className="mb-6 relative z-10">
          <AgentBadge agentName={activeAgent} />
        </div>
      )}

      {lastUserMsg && (
        <div className="mb-6 max-w-md text-center relative z-10">
          <p className="text-[10px] uppercase tracking-widest text-gray-600 mb-1.5">You said</p>
          <p className="text-sm text-gray-300 line-clamp-2">{lastUserMsg.content}</p>
        </div>
      )}

      {/* Siri-like Orb */}
      <button
        onClick={handleMainClick}
        className="relative z-10 group focus:outline-none"
      >
        {/* Outer rings */}
        <div
          className={clsx(
            "absolute inset-0 rounded-full transition-all duration-700",
            orbState === "recording" && "animate-ping bg-red-500/30 scale-150",
            orbState === "processing" && "animate-spin-slow bg-gradient-to-r from-[#6565FF]/20 to-[#3535F3]/20 scale-125",
            orbState === "speaking" && "animate-pulse bg-[#5555F7]/25 scale-140",
          )}
          style={{ margin: "-20px" }}
        />
        <div
          className={clsx(
            "absolute inset-0 rounded-full transition-all duration-500",
            orbState === "recording" && "animate-pulse bg-red-500/20 scale-130",
            orbState === "speaking" && "animate-pulse bg-[#5555F7]/15 scale-120 animation-delay-200",
          )}
          style={{ margin: "-10px" }}
        />

        {/* Main orb */}
        <div
          className={clsx(
            "w-32 h-32 rounded-full flex items-center justify-center transition-all duration-500 relative",
            "shadow-2xl",
            orbState === "idle" && "bg-gradient-to-br from-[#3535F3] via-[#2828D0] to-[#1e1ea0] hover:scale-105 hover:shadow-[#3535F3]/30 shadow-[#3535F3]/20",
            orbState === "idle-active" && "bg-gradient-to-br from-gray-600 via-gray-700 to-gray-800 hover:scale-105 shadow-gray-500/20",
            orbState === "recording" && "bg-gradient-to-br from-red-500 via-red-600 to-rose-700 scale-110 shadow-red-500/40",
            orbState === "processing" && "bg-gradient-to-br from-[#5555F7] via-[#4747F5] to-[#3535F3] shadow-[#3535F3]/40",
            orbState === "speaking" && "bg-gradient-to-br from-[#4747F5] via-[#3535F3] to-[#2828D0] scale-105 shadow-[#3535F3]/40",
          )}
        >
          {/* Inner glow */}
          <div
            className={clsx(
              "absolute inset-2 rounded-full opacity-30",
              "bg-gradient-to-t from-transparent to-white/20",
            )}
          />

          {/* Waveform visualization inside orb */}
          {(isRecording || isSpeaking) && (
            <div className="flex items-center gap-[3px] relative z-10">
              {[0, 1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className={clsx(
                    "w-[3px] rounded-full",
                    isRecording ? "bg-white/90" : "bg-white/80",
                  )}
                  style={{
                    height: `${14 + Math.random() * 28}px`,
                    animation: `voiceBar 0.6s ease-in-out ${i * 0.08}s infinite alternate`,
                  }}
                />
              ))}
            </div>
          )}

          {isProcessing && (
            <div className="relative z-10">
              <div className="w-10 h-10 border-[3px] border-white/30 border-t-white rounded-full animate-spin" />
            </div>
          )}

          {orbState === "idle" && (
            <div className="relative z-10 flex flex-col items-center gap-1">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-white" />
              </div>
            </div>
          )}

          {orbState === "idle-active" && (
            <div className="relative z-10 text-white/80 text-xs font-semibold">
              TAP
            </div>
          )}
        </div>
      </button>

      {/* Status text */}
      <p
        className={clsx(
          "mt-8 text-sm font-medium relative z-10 transition-colors duration-300",
          error ? "text-red-400" : "text-gray-400",
        )}
      >
        {statusText}
      </p>

      {isLoopActive && !isRecording && !isProcessing && !isSpeaking && (
        <p className="mt-2 text-[10px] uppercase tracking-widest text-gray-600 relative z-10">
          Tap orb to end
        </p>
      )}

      {/* Last agent response */}
      {lastAssistantMsg && !isRecording && (
        <div className="mt-8 max-w-lg text-center relative z-10">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Volume2 className="w-3 h-3 text-gray-600" />
            <p className="text-[10px] uppercase tracking-widest text-gray-600">Agent response</p>
          </div>
          <p className="text-sm text-gray-400 line-clamp-3 leading-relaxed">
            {lastAssistantMsg.content}
          </p>
        </div>
      )}

      {/* CSS for voice bars animation */}
      <style>{`
        @keyframes voiceBar {
          0% { transform: scaleY(0.4); }
          100% { transform: scaleY(1); }
        }
      `}</style>
    </div>
  );
}
