import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import { User, Bot } from "lucide-react";
import type { Message } from "../../types/chat";
import AgentBadge from "../agents/AgentBadge";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={clsx("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      {/* Agent avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center flex-shrink-0 mt-1 shadow-lg shadow-blue-500/20">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}

      <div className={clsx("max-w-[75%] flex flex-col gap-1")}>
        {/* Agent badge */}
        {message.agentName && !isUser && (
          <div className="mb-0.5">
            <AgentBadge agentName={message.agentName} />
          </div>
        )}

        {/* Bubble */}
        <div
          className={clsx(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-br-md"
              : "bg-gray-800/80 text-gray-100 border border-gray-700/40 rounded-bl-md",
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:mb-2 [&>ol]:mb-2">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-600 to-gray-700 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-4 h-4 text-gray-300" />
        </div>
      )}
    </div>
  );
}
