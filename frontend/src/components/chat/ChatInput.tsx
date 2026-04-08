import { useState, useEffect, type FormEvent } from "react";
import { useVoiceInput } from "../../hooks/useVoiceInput";
import VoiceButton from "./VoiceButton";

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState("");
  const { isRecording, isTranscribing, transcript, startRecording, stopRecording, clearTranscript } =
    useVoiceInput();

  // When transcript arrives, put it in the input
  useEffect(() => {
    if (transcript) {
      setInput((prev) => (prev ? prev + " " + transcript : transcript));
      clearTranscript();
    }
  }, [transcript, clearTranscript]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const handleVoiceToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-800 p-4">
      <div className="flex gap-2 items-center">
        <VoiceButton
          isRecording={isRecording}
          isTranscribing={isTranscribing}
          onToggle={handleVoiceToggle}
        />
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isRecording ? "Listening..." : "Type a message..."}
          disabled={disabled || isRecording}
          className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim() || isRecording}
          className="px-4 py-2 bg-blue-600 rounded-xl text-sm hover:bg-blue-700 disabled:opacity-50 transition"
        >
          Send
        </button>
      </div>
    </form>
  );
}
