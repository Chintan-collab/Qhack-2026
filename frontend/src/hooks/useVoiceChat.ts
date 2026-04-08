import { useCallback, useRef, useState } from "react";
import { useChatStore } from "../store/chatStore";
import type { Message } from "../types/chat";

const VOICE_CHAT_URL = "/api/v1/voice/chat";

interface VoiceChatState {
  isRecording: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  error: string | null;
}

interface VoiceChatResponse {
  transcript: string;
  reply: string;
  conversation_id: string;
  agent_name?: string;
  phase?: string;
}

/**
 * Speak text using the browser's built-in SpeechSynthesis API.
 * Returns a promise that resolves when speech finishes.
 */
function speakText(text: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!("speechSynthesis" in window)) {
      reject(new Error("Speech synthesis not supported"));
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Try to pick a natural-sounding voice
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(
      (v) =>
        v.lang.startsWith("en") &&
        (v.name.includes("Google") ||
          v.name.includes("Natural") ||
          v.name.includes("Samantha") ||
          v.name.includes("Daniel")),
    );
    if (preferred) utterance.voice = preferred;

    utterance.onend = () => resolve();
    utterance.onerror = (e) => reject(e);

    window.speechSynthesis.speak(utterance);
  });
}

/**
 * Full voice mode: record → Gemini transcribe → agent → browser TTS.
 * Audio in, audio out. No text input needed.
 */
export function useVoiceChat(projectId?: string) {
  const store = useChatStore();
  const [state, setState] = useState<VoiceChatState>({
    isRecording: false,
    isProcessing: false,
    isSpeaking: false,
    error: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

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

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis.cancel();
    setState((s) => ({ ...s, isSpeaking: false }));
  }, []);

  const processVoiceRoundTrip = useCallback(
    async (audioBlob: Blob) => {
      setState((s) => ({ ...s, isProcessing: true }));

      try {
        // Send audio to backend (Gemini STT + agent pipeline)
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");
        if (store.activeConversationId) {
          formData.append("conversation_id", store.activeConversationId);
        }
        if (projectId) {
          formData.append("project_id", projectId);
        }

        const response = await fetch(VOICE_CHAT_URL, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Voice chat failed: ${response.statusText}`);
        }

        const data: VoiceChatResponse = await response.json();

        // Update store
        if (data.conversation_id && !store.activeConversationId) {
          store.setActiveConversation(data.conversation_id);
        }
        if (data.phase) {
          store.setCurrentPhase(data.phase);
        }

        // Add messages to history
        const userMsg: Message = {
          id: crypto.randomUUID(),
          role: "user",
          content: data.transcript,
          timestamp: new Date().toISOString(),
          metadata: { voice: true },
        };
        const assistantMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.reply,
          agentName: data.agent_name,
          timestamp: new Date().toISOString(),
          metadata: { voice: true, phase: data.phase },
        };
        store.addMessage(userMsg);
        store.addMessage(assistantMsg);

        // Speak the response using browser TTS
        setState((s) => ({
          ...s,
          isProcessing: false,
          isSpeaking: true,
        }));

        try {
          await speakText(data.reply);
        } catch {
          // TTS failed silently — text is still in message history
        }

        setState((s) => ({ ...s, isSpeaking: false }));
      } catch (e) {
        setState((s) => ({
          ...s,
          isProcessing: false,
          error: e instanceof Error ? e.message : "Voice chat failed",
        }));
      }
    },
    [store, projectId],
  );

  return {
    ...state,
    startRecording,
    stopRecording,
    stopSpeaking,
    messages: store.messages,
    activeAgent: store.activeAgent,
    currentPhase: store.currentPhase,
  };
}
