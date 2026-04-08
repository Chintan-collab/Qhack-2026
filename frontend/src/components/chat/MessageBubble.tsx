import clsx from "clsx";
import type { Message } from "../../types/chat";

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
          <div className="text-xs text-gray-400 mb-1">{message.agentName}</div>
        )}
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
