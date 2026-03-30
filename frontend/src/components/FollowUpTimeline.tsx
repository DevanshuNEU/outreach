import { Check, Clock, AlertCircle, PartyPopper } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Outreach {
  id: string;
  sent_at: string | null;
  followup_1_sent_at: string | null;
  followup_2_sent_at: string | null;
  followup_3_sent_at: string | null;
  replied: boolean;
}

interface Props {
  outreach: Outreach;
  onMarkSent: (outreachId: string, field: string) => void;
}

const STEPS = [
  { label: "Initial", days: 0, field: "sent_at" },
  { label: "FU1", days: 3, field: "followup_1_sent_at" },
  { label: "FU2", days: 10, field: "followup_2_sent_at" },
  { label: "FU3", days: 17, field: "followup_3_sent_at" },
] as const;

function daysFromNow(dateStr: string, addDays: number): number {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + addDays);
  const now = new Date();
  return Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

export function FollowUpTimeline({ outreach, onMarkSent }: Props) {
  if (!outreach.sent_at) return null;

  if (outreach.replied) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
        <PartyPopper className="h-4 w-4 text-green-600" />
        <span className="text-sm font-medium text-green-700 dark:text-green-400">
          Got a reply!
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1 py-2">
      {STEPS.map((step, i) => {
        const isSent = !!outreach[step.field as keyof Outreach];
        const daysUntil = daysFromNow(outreach.sent_at!, step.days);
        const isDue = !isSent && i > 0 && daysUntil <= 0;
        const isOverdue = !isSent && i > 0 && daysUntil < 0;
        const isUpcoming = !isSent && i > 0 && daysUntil > 0;
        // Is this the next actionable step?
        const prevSent = i === 0 || !!outreach[STEPS[i - 1].field as keyof Outreach];
        const isNext = !isSent && i > 0 && prevSent;

        return (
          <div key={step.field} className="flex items-center gap-1">
            {/* Connector line */}
            {i > 0 && (
              <div
                className={`h-0.5 w-4 ${
                  isSent ? "bg-green-400" : isDue || isOverdue ? "bg-orange-300" : "bg-gray-200"
                }`}
              />
            )}

            {/* Step circle + label */}
            <div className="flex flex-col items-center gap-0.5">
              <div className="flex items-center gap-1.5">
                {isSent ? (
                  <div className="h-5 w-5 rounded-full bg-green-500 flex items-center justify-center">
                    <Check className="h-3 w-3 text-white" />
                  </div>
                ) : isDue || isOverdue ? (
                  <div className="h-5 w-5 rounded-full bg-orange-500 flex items-center justify-center animate-pulse">
                    <AlertCircle className="h-3 w-3 text-white" />
                  </div>
                ) : (
                  <div className="h-5 w-5 rounded-full border-2 border-gray-300 flex items-center justify-center">
                    <Clock className="h-3 w-3 text-gray-400" />
                  </div>
                )}

                <span
                  className={`text-xs font-medium ${
                    isSent ? "text-green-700 dark:text-green-400" :
                    isDue || isOverdue ? "text-orange-700 dark:text-orange-400" :
                    "text-gray-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Status text */}
              {i === 0 && isSent && (
                <span className="text-[10px] text-muted-foreground">Sent</span>
              )}
              {i > 0 && isSent && (
                <span className="text-[10px] text-green-600">Sent</span>
              )}
              {isOverdue && (
                <span className="text-[10px] text-red-600 font-medium">
                  {Math.abs(daysUntil)}d overdue
                </span>
              )}
              {isDue && !isOverdue && (
                <span className="text-[10px] text-orange-600 font-medium">Due today</span>
              )}
              {isUpcoming && isNext && (
                <span className="text-[10px] text-muted-foreground">
                  In {daysUntil}d
                </span>
              )}

              {/* Mark Sent button */}
              {isNext && (isDue || isOverdue) && (
                <Button
                  size="sm"
                  variant="outline"
                  className="h-5 px-1.5 text-[10px]"
                  onClick={() => onMarkSent(outreach.id, step.field)}
                >
                  Mark Sent
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
