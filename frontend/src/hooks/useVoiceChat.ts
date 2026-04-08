import { useCallback, useRef, useState } from "react";
import { useChatStore } from "../store/chatStore";
import type { Message } from "../types/chat";

const VOICE_CHAT_URL = "/api/v1/voice/chat";

interface VoiceChatState {
  isRecording: boolean;
  isProcessing: boolean;
  isPlaying: boolean;
  error: string | null;
}

/**
 * Full voice mode hook: record → transcribe → agent → TTS → playback.
 * One mic press = one full round-trip. No text shown during voice mode,
 * everything is audio in / audio out.
 */
export function useVoiceChat(projectId?: string) {
  const store = useChatStore();
  const [state, setState] = useState<VoiceChatState>({
    isRecording: false,
    isProcessing: false,
    isPlaying: false,
    error: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const startRecording = useCallback(async () => {
    setState((s) => ({ ...s, isRecording: true, error: null }));

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, {
          type: "audio/webm",
        });
        await processVoiceRoundTrip(blob);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
    } catch {
      setState((s) => ({
        ...s,
        isRecording: false,
        error: "Microphone access denied",
      }));
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setState((s) => ({ ...s, isRecording: false }));
  }, []);

  const stopPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setState((s) => ({ ...s, isPlaying: false }));
  }, []);

  const processVoiceRoundTrip = useCallback(
    async (audioBlob: Blob) => {
      setState((s) => ({ ...s, isProcessing: true }));

      try {
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");
        if (store.activeConversationId) {
          formData.append(
            "conversation_id",
            store.activeConversationId,
          );
        }
        if (projectId) {
          formData.append("project_id", projectId);
        }

        const response = await fetch(VOICE_CHAT_URL, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error(
            `Voice chat failed: ${response.statusText}`,
          );
        }

        // Read metadata from headers
        const transcript =
          response.headers.get("X-Transcript") ?? "";
        const agentReply =
          response.headers.get("X-Agent-Reply") ?? "";
        const conversationId =
          response.headers.get("X-Conversation-Id") ?? "";
        const agentName =
          response.headers.get("X-Agent-Name") ?? undefined;
        const phase =
          response.headers.get("X-Phase") ?? undefined;

        // Update conversation ID
        if (conversationId && !store.activeConversationId) {
          store.setActiveConversation(conversationId);
        }

        // Update phase
        if (phase) {
          store.setCurrentPhase(phase);
        }

        // Add messages to store (visible in message history)
        const userMsg: Message = {
          id: crypto.randomUUID(),
          role: "user",
          content: transcript,
          timestamp: new Date().toISOString(),
          metadata: { voice: true },
        };
        const assistantMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: agentReply,
          agentName: agentName,
          timestamp: new Date().toISOString(),
          metadata: { voice: true, phase },
        };
        store.addMessage(userMsg);
        store.addMessage(assistantMsg);

        // Play the audio response
        const audioBlob2 = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob2);
        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        setState((s) => ({
          ...s,
          isProcessing: false,
          isPlaying: true,
        }));

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          audioRef.current = null;
          setState((s) => ({ ...s, isPlaying: false }));
        };

        audio.play();
      } catch (e) {
        setState((s) => ({
          ...s,
          isProcessing: false,
          error:
            e instanceof Error
              ? e.message
              : "Voice chat failed",
        }));
      }
    },
    [store, projectId],
  );

  return {
    ...state,
    startRecording,
    stopRecording,
    stopPlayback,
    messages: store.messages,
    activeAgent: store.activeAgent,
    currentPhase: store.currentPhase,
  };
}
