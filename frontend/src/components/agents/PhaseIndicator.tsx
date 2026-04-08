import clsx from "clsx";

const PHASES = [
  { key: "gathering", label: "Data Gathering" },
  { key: "researching", label: "Research" },
  { key: "strategizing", label: "Strategy" },
  { key: "complete", label: "Pitch Deck" },
];

interface Props {
  status: string;
}

export default function PhaseIndicator({ status }: Props) {
  const currentIndex = PHASES.findIndex((p) => p.key === status);

  return (
    <div className="flex items-center gap-1">
      {PHASES.map((phase, i) => {
        const isComplete = i < currentIndex;
        const isCurrent = i === currentIndex;

        return (
          <div key={phase.key} className="flex items-center gap-1 flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={clsx(
                  "w-full h-1.5 rounded-full transition-colors",
                  isComplete && "bg-blue-500",
                  isCurrent && "bg-blue-500 animate-pulse",
                  !isComplete && !isCurrent && "bg-gray-700",
                )}
              />
              <span
                className={clsx(
                  "text-xs mt-1.5 transition-colors",
                  isCurrent ? "text-white font-medium" : "text-gray-500",
                )}
              >
                {phase.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
