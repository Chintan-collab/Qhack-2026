import { useRef, useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { Send, Paperclip, Check, Loader2 } from "lucide-react";

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
  projectId?: string;
}

export default function ChatInput({ onSend, disabled, projectId }: Props) {
  const [input, setInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [autoProjectId, setAutoProjectId] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const effectiveProjectId = projectId || autoProjectId;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const ensureProjectForUpload = async (): Promise<string> => {
    if (effectiveProjectId) return effectiveProjectId;

    // Create a blank project for doc uploads
    const res = await fetch(
      `${import.meta.env.VITE_API_URL || ""}/api/v1/projects/`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "New Lead" }),
      },
    );
    const project = await res.json();
    setAutoProjectId(project.id);
    return project.id;
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadedFile(null);
    try {
      const pid = await ensureProjectForUpload();
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || ""}/api/v1/documents/upload/${pid}`,
        { method: "POST", body: formData },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Upload failed");
      } else {
        setUploadedFile(file.name);
        setTimeout(() => setUploadedFile(null), 4000);
      }
    } catch {
      alert("Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <form onSubmit={handleSubmit} className="shrink-0 p-4" style={{ background: "rgba(255,255,255,0.9)", backdropFilter: "blur(12px)", borderTop: "1px solid #e5e7eb" }}>
      {uploadedFile && (
        <div className="max-w-3xl mx-auto mb-2 flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs" style={{ background: "rgba(53,53,243,0.06)", color: "#3535F3" }}>
          <Check className="w-3.5 h-3.5" />
          <span><strong>{uploadedFile}</strong> uploaded — Cleo will use it in research</span>
        </div>
      )}

      <div className="flex gap-2 items-center max-w-3xl mx-auto">
        {/* PDF upload button — always visible */}
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          onChange={handleFileUpload}
          className="hidden"
        />
        <motion.button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={uploading || disabled}
          className="rounded-xl transition flex items-center justify-center disabled:opacity-30"
          style={{
            width: "42px",
            height: "42px",
            background: "#f8f9fb",
            border: "1px solid #e5e7eb",
            color: "#64748b",
            cursor: uploading ? "not-allowed" : "pointer",
            flexShrink: 0,
          }}
          whileHover={{ borderColor: "#3535F3", color: "#3535F3" }}
          whileTap={{ scale: 0.95 }}
          title="Upload PDF"
        >
          {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Paperclip className="w-4 h-4" />}
        </motion.button>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          disabled={disabled}
          className="flex-1 rounded-xl px-4 py-3 text-sm focus:outline-none transition-all duration-200"
          style={{
            background: "#ffffff",
            border: "1px solid #e5e7eb",
            color: "#0f172a",
          }}
          onFocus={(e) => {
            e.target.style.borderColor = "rgba(53,53,243,0.5)";
            e.target.style.boxShadow = "0 0 0 3px rgba(53,53,243,0.1)";
          }}
          onBlur={(e) => {
            e.target.style.borderColor = "#e5e7eb";
            e.target.style.boxShadow = "none";
          }}
        />
        <motion.button
          type="submit"
          disabled={disabled || !input.trim()}
          className="rounded-xl text-sm font-medium disabled:opacity-30 transition flex items-center gap-1.5"
          style={{
            padding: "12px 20px",
            background: "#3535F3",
            color: "#fff",
            border: "none",
            cursor: disabled || !input.trim() ? "not-allowed" : "pointer",
          }}
          whileTap={{ scale: 0.9 }}
          whileHover={{ scale: 1.03 }}
        >
          <Send className="w-4 h-4" />
          Send
        </motion.button>
      </div>
    </form>
  );
}
