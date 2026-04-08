import clsx from "clsx";
import { ClipboardList, Search, Lightbulb, FileText, Check } from "lucide-react";

const PHASES = [
  { key: "gathering", label: "Gathering", icon: ClipboardList },
  { key: "researching", label: "Research", icon: Search },
  { key: "strategizing", label: "Strategy", icon: Lightbulb },
  { key: "complete", label: "Report", icon: FileText },
];

interface Props {
  status: string;
}

export default function PhaseIndicator({ status }: Props) {
  const currentIndex = PHASES.findIndex((p) => p.key === status);

  return (
    <div className="flex items-center w-full gap-0">
      {PHASES.map((phase, i) => {
        const isComplete = i < currentIndex;
        const isCurrent = i === currentIndex;
        const Icon = phase.icon;

        return (
          <div key={phase.key} className="flex items-center flex-1">
            {/* Step circle */}
            <div className="flex flex-col items-center gap-1.5 relative z-10">
              <div
                className={clsx(
                  "w-9 h-9 rounded-full flex items-center justify-center transition-all duration-500 border-2",
                  isComplete && "bg-emerald-500 border-emerald-500 text-white scale-100",
                  isCurrent && "bg-blue-600 border-blue-400 text-white scale-110 shadow-lg shadow-blue-500/40",
                  !isComplete && !isCurrent && "bg-gray-800 border-gray-600 text-gray-500",
                )}
              >
                {isComplete ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
              </div>
              <span
                className={clsx(
                  "text-[10px] font-semibold tracking-wide uppercase transition-colors duration-300",
                  isComplete && "text-emerald-400",
                  isCurrent && "text-blue-400",
                  !isComplete && !isCurrent && "text-gray-600",
                )}
              >
                {phase.label}
              </span>
            </div>

            {/* Connector line */}
            {i < PHASES.length - 1 && (
              <div className="flex-1 h-0.5 mx-1 rounded-full relative overflow-hidden bg-gray-700">
                <div
                  className={clsx(
                    "absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out",
                    isComplete ? "w-full bg-emerald-500" : isCurrent ? "w-1/2 bg-blue-500 animate-pulse" : "w-0",
                  )}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
