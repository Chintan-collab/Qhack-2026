import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import type { Message } from "../../types/chat";
import AgentBadge from "../agents/AgentBadge";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={clsx("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[70%] rounded-2xl px-4 py-2 text-sm",
          isUser ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100",
        )}
      >
        {message.agentName && (
          <div className="mb-1">
            <AgentBadge agentName={message.agentName} />
          </div>
        )}
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
