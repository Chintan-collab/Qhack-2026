import { Mic, MicOff, Loader2, Volume2, CircleStop } from "lucide-react";
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
    error,
    startRecording,
    stopRecording,
    stopSpeaking,
    messages,
    activeAgent,
  } = useVoiceChat(projectId);

  const lastAssistantMsg = [...messages]
    .reverse()
    .find((m) => m.role === "assistant");
  const lastUserMsg = [...messages]
    .reverse()
    .find((m) => m.role === "user");

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else if (isSpeaking) {
      stopSpeaking();
    } else if (!isProcessing) {
      startRecording();
    }
  };

  let statusText = "Tap to speak";
  if (isRecording) statusText = "Listening...";
  if (isProcessing) statusText = "Thinking...";
  if (isSpeaking) statusText = "Speaking...";
  if (error) statusText = error;

  return (
    <div className="flex flex-col items-center justify-center flex-1 px-8">
      {activeAgent && (
        <div className="mb-8">
          <AgentBadge agentName={activeAgent} />
        </div>
      )}

      {lastUserMsg && (
        <div className="mb-4 max-w-md text-center">
          <p className="text-xs text-gray-500 mb-1">You said:</p>
          <p className="text-sm text-gray-300 line-clamp-2">
            {lastUserMsg.content}
          </p>
        </div>
      )}

      <button
        onClick={handleMicClick}
        disabled={isProcessing}
        className={clsx(
          "w-24 h-24 rounded-full flex items-center justify-center transition-all",
          "focus:outline-none focus:ring-4 focus:ring-blue-500/30",
          isRecording && "bg-red-600 scale-110 animate-pulse",
          isProcessing && "bg-gray-700 cursor-not-allowed",
          isSpeaking && "bg-purple-600 scale-105",
          !isRecording && !isProcessing && !isSpeaking && "bg-blue-600 hover:bg-blue-500 hover:scale-105",
        )}
      >
        {isProcessing ? (
          <Loader2 className="w-10 h-10 animate-spin" />
        ) : isRecording ? (
          <MicOff className="w-10 h-10" />
        ) : isSpeaking ? (
          <CircleStop className="w-10 h-10" />
        ) : (
          <Mic className="w-10 h-10" />
        )}
      </button>

      <p
        className={clsx(
          "mt-6 text-sm",
          error ? "text-red-400" : "text-gray-400",
        )}
      >
        {statusText}
      </p>

      {isRecording && (
        <div className="mt-4 flex gap-1.5">
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="w-1 bg-red-500 rounded-full animate-pulse"
              style={{
                height: `${12 + Math.random() * 20}px`,
                animationDelay: `${i * 0.1}s`,
              }}
            />
          ))}
        </div>
      )}

      {isSpeaking && (
        <div className="mt-4 flex gap-1.5">
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="w-1 bg-purple-500 rounded-full animate-pulse"
              style={{
                height: `${12 + Math.random() * 20}px`,
                animationDelay: `${i * 0.15}s`,
              }}
            />
          ))}
        </div>
      )}

      {lastAssistantMsg && !isRecording && (
        <div className="mt-8 max-w-lg text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Volume2 className="w-3 h-3 text-gray-500" />
            <p className="text-xs text-gray-500">Agent said:</p>
          </div>
          <p className="text-sm text-gray-400 line-clamp-3">
            {lastAssistantMsg.content}
          </p>
        </div>
      )}
    </div>
  );
}
