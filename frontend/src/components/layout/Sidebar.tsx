import { Link } from "react-router-dom";
import { useChatStore } from "../../store/chatStore";

export default function Sidebar() {
  const conversations = useChatStore((s) => s.conversations);

  return (
    <aside className="w-64 border-r border-gray-800 flex flex-col p-4">
      <Link
        to="/"
        className="mb-4 px-3 py-2 bg-blue-600 rounded-lg text-center hover:bg-blue-700 transition"
      >
        New Chat
      </Link>
      <nav className="flex-1 overflow-y-auto space-y-1">
        {conversations.map((conv) => (
          <Link
            key={conv.id}
            to={`/chat/${conv.id}`}
            className="block px-3 py-2 rounded-lg hover:bg-gray-800 truncate text-sm"
          >
            {conv.title}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
