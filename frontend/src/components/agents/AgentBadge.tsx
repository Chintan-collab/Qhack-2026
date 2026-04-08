import clsx from "clsx";

const AGENT_STYLES: Record<string, { color: string; label: string }> = {
  data_gathering: { color: "bg-blue-600", label: "Data Gathering" },
  research: { color: "bg-green-600", label: "Research" },
  strategy: { color: "bg-orange-500", label: "Strategy" },
  pitch_deck: { color: "bg-purple-600", label: "Pitch Deck" },
};

interface Props {
  agentName: string;
  className?: string;
}

export default function AgentBadge({ agentName, className }: Props) {
  const style = AGENT_STYLES[agentName] ?? { color: "bg-gray-600", label: agentName };

  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
        style.color,
        className,
      )}
    >
      {style.label}
    </span>
  );
}
