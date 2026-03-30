import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bell, CheckCircle } from "lucide-react";
import api from "@/lib/api";

interface QueueItem {
  outreach_id: string;
  application_id: string;
  followup_number: number;
  followup_field: string;
  due_date: string;
  days_until: number;
  is_overdue: boolean;
  contact_name: string;
  contact_email: string;
  company_name: string;
  job_title: string;
}

interface QueueData {
  overdue: QueueItem[];
  due_today: QueueItem[];
  upcoming: QueueItem[];
  total_due: number;
}

export function FollowUpQueueCard() {
  const [data, setData] = useState<QueueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState<string | null>(null);

  const load = () => {
    api
      .get("/api/followup-queue")
      .then((r) => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleMarkSent = async (item: QueueItem) => {
    setMarking(item.outreach_id);
    try {
      await api.put(`/api/outreach/${item.outreach_id}`, {
        [item.followup_field]: new Date().toISOString(),
      });
      load();
    } catch {}
    setMarking(null);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Bell className="h-4 w-4" /> Follow-Up Queue
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </CardContent>
      </Card>
    );
  }

  const allItems = [
    ...(data?.overdue || []),
    ...(data?.due_today || []),
    ...(data?.upcoming || []),
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Bell className="h-4 w-4" />
          Follow-Up Queue
          {data && data.total_due > 0 && (
            <Badge className="bg-orange-100 text-orange-800 ml-auto">
              {data.total_due} due
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {allItems.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            All caught up! No follow-ups due.
          </div>
        ) : (
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {allItems.map((item) => (
              <div
                key={`${item.outreach_id}-${item.followup_number}`}
                className={`flex items-center justify-between gap-2 p-2 rounded-md border text-sm ${
                  item.is_overdue && item.days_until < 0
                    ? "border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-800"
                    : item.days_until === 0
                    ? "border-orange-200 bg-orange-50 dark:bg-orange-950/20 dark:border-orange-800"
                    : "border-gray-200 dark:border-gray-700"
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <Badge
                      className={`text-[10px] px-1.5 ${
                        item.is_overdue
                          ? "bg-red-100 text-red-800"
                          : item.days_until === 0
                          ? "bg-orange-100 text-orange-800"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      FU{item.followup_number}
                    </Badge>
                    <span className="font-medium truncate">{item.company_name}</span>
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {item.contact_name} · {item.job_title || "No title"}
                    {item.days_until < 0 && (
                      <span className="text-red-600 ml-1">
                        {Math.abs(item.days_until)}d overdue
                      </span>
                    )}
                    {item.days_until > 0 && (
                      <span className="text-muted-foreground ml-1">
                        in {item.days_until}d
                      </span>
                    )}
                    {item.days_until === 0 && (
                      <span className="text-orange-600 ml-1">today</span>
                    )}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs shrink-0"
                  disabled={marking === item.outreach_id}
                  onClick={() => handleMarkSent(item)}
                >
                  {marking === item.outreach_id ? "..." : "Mark Sent"}
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
