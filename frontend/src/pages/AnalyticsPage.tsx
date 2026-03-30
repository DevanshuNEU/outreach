import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";

interface RateRow {
  label?: string;
  slug?: string;
  title?: string;
  seniority?: string;
  day?: string;
  stage?: string;
  sent: number;
  replied: number;
  rate: number;
}

interface Analytics {
  by_company_size: RateRow[];
  by_template: RateRow[];
  by_seniority: RateRow[];
  time_to_reply: {
    avg: number | null;
    median: number | null;
    min: number | null;
    max: number | null;
    count: number;
  };
  followup_effectiveness: { stage: string; replies: number; pct: number }[];
  optimal_contacts: {
    contacts: number;
    applications: number;
    replied: number;
    rate: number;
  }[];
  weekly_activity: { week: string; sent: number; replied: number }[];
  best_day: RateRow[];
  pipeline_funnel: { stage: string; count: number }[];
  monthly_trends: {
    month: string;
    applications: number;
    sent: number;
    replied: number;
  }[];
  totals: { total_sent: number; total_replied: number; response_rate: number };
}

function Bar({
  value,
  max,
  color = "bg-blue-500",
}: {
  value: number;
  max: number;
  color?: string;
}) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
      <div
        className={`h-full ${color} rounded-full transition-all`}
        style={{ width: `${Math.max(pct, 2)}%` }}
      />
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <p className="text-sm text-muted-foreground text-center py-4">{text}</p>
  );
}

export function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/analytics")
      .then((r) => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading analytics...</p>;
  if (!data) return <p>Failed to load analytics.</p>;

  const maxSent = Math.max(
    ...data.by_company_size.map((r) => r.sent),
    ...data.by_template.map((r) => r.sent),
    1
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>

      {/* Top-level totals */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold">{data.totals.total_sent}</p>
            <p className="text-xs text-muted-foreground">Emails Sent</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold">{data.totals.total_replied}</p>
            <p className="text-xs text-muted-foreground">Replies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold">{data.totals.response_rate}%</p>
            <p className="text-xs text-muted-foreground">Response Rate</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* 1. By Company Size */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Reply Rate by Company Size</CardTitle>
          </CardHeader>
          <CardContent>
            {data.by_company_size.length === 0 ? (
              <EmptyState text="Send emails to see data here" />
            ) : (
              <div className="space-y-3">
                {data.by_company_size.map((r) => (
                  <div key={r.label}>
                    <div className="flex justify-between text-xs mb-1">
                      <span>{r.label}</span>
                      <span className="text-muted-foreground">
                        {r.replied}/{r.sent} ({r.rate}%)
                      </span>
                    </div>
                    <Bar value={r.sent} max={maxSent} />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 2. By Template */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Reply Rate by Template</CardTitle>
          </CardHeader>
          <CardContent>
            {data.by_template.length === 0 ? (
              <EmptyState text="Send emails to see data here" />
            ) : (
              <div className="space-y-3">
                {data.by_template.map((r) => (
                  <div key={r.slug}>
                    <div className="flex justify-between text-xs mb-1">
                      <span>{r.title}</span>
                      <span className="text-muted-foreground">
                        {r.replied}/{r.sent} ({r.rate}%)
                      </span>
                    </div>
                    <Bar value={r.sent} max={maxSent} color="bg-purple-500" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 3. By Seniority */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Reply Rate by Seniority</CardTitle>
          </CardHeader>
          <CardContent>
            {data.by_seniority.length === 0 ? (
              <EmptyState text="Send emails to see data here" />
            ) : (
              <div className="space-y-3">
                {data.by_seniority.map((r) => (
                  <div key={r.seniority}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="capitalize">{r.seniority}</span>
                      <span className="text-muted-foreground">
                        {r.replied}/{r.sent} ({r.rate}%)
                      </span>
                    </div>
                    <Bar
                      value={r.sent}
                      max={Math.max(...data.by_seniority.map((s) => s.sent), 1)}
                      color="bg-green-500"
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 4. Time to Reply */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Time to Reply</CardTitle>
          </CardHeader>
          <CardContent>
            {data.time_to_reply.count === 0 ? (
              <EmptyState text="No replies yet to measure" />
            ) : (
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold">{data.time_to_reply.avg}d</p>
                  <p className="text-xs text-muted-foreground">Average</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{data.time_to_reply.median}d</p>
                  <p className="text-xs text-muted-foreground">Median</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{data.time_to_reply.min}d</p>
                  <p className="text-xs text-muted-foreground">Fastest</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{data.time_to_reply.max}d</p>
                  <p className="text-xs text-muted-foreground">Slowest</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 5. Follow-Up Effectiveness */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Which Follow-Up Gets Replies?</CardTitle>
          </CardHeader>
          <CardContent>
            {data.followup_effectiveness.every((f) => f.replies === 0) ? (
              <EmptyState text="No replies yet" />
            ) : (
              <div className="space-y-3">
                {data.followup_effectiveness.map((f) => (
                  <div key={f.stage}>
                    <div className="flex justify-between text-xs mb-1">
                      <span>{f.stage}</span>
                      <span className="text-muted-foreground">
                        {f.replies} replies ({f.pct}%)
                      </span>
                    </div>
                    <Bar
                      value={f.replies}
                      max={Math.max(
                        ...data.followup_effectiveness.map((x) => x.replies),
                        1
                      )}
                      color="bg-orange-500"
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 6. Optimal Contacts */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Optimal Contacts per Company</CardTitle>
          </CardHeader>
          <CardContent>
            {data.optimal_contacts.length === 0 ? (
              <EmptyState text="Send emails to see data here" />
            ) : (
              <div className="space-y-3">
                {data.optimal_contacts.map((r) => (
                  <div key={r.contacts}>
                    <div className="flex justify-between text-xs mb-1">
                      <span>
                        {r.contacts} contact{r.contacts !== 1 ? "s" : ""}
                      </span>
                      <span className="text-muted-foreground">
                        {r.replied}/{r.applications} apps replied ({r.rate}%)
                      </span>
                    </div>
                    <Bar
                      value={r.applications}
                      max={Math.max(
                        ...data.optimal_contacts.map((x) => x.applications),
                        1
                      )}
                      color="bg-cyan-500"
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 7. Weekly Activity */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Weekly Activity (Last 8 Weeks)</CardTitle>
          </CardHeader>
          <CardContent>
            {data.weekly_activity.length === 0 ? (
              <EmptyState text="No activity yet" />
            ) : (
              <div className="space-y-2">
                {data.weekly_activity.map((w) => (
                  <div key={w.week} className="flex items-center gap-3 text-xs">
                    <span className="w-16 text-muted-foreground">{w.week}</span>
                    <div className="flex-1">
                      <Bar
                        value={w.sent}
                        max={Math.max(
                          ...data.weekly_activity.map((x) => x.sent),
                          1
                        )}
                        color="bg-blue-500"
                      />
                    </div>
                    <span className="w-20 text-right">
                      {w.sent} sent, {w.replied} replies
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 8. Best Day to Send */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Best Day to Send</CardTitle>
          </CardHeader>
          <CardContent>
            {data.best_day.length === 0 ? (
              <EmptyState text="Send emails to see data here" />
            ) : (
              <div className="space-y-2">
                {data.best_day.map((d) => (
                  <div key={d.day} className="flex items-center gap-3 text-xs">
                    <span className="w-20">{d.day}</span>
                    <div className="flex-1">
                      <Bar
                        value={d.sent}
                        max={Math.max(...data.best_day.map((x) => x.sent), 1)}
                        color={d.rate > 0 ? "bg-green-500" : "bg-gray-400"}
                      />
                    </div>
                    <span className="w-24 text-right text-muted-foreground">
                      {d.sent} sent ({d.rate}%)
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 9. Pipeline Funnel */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Pipeline Funnel</CardTitle>
          </CardHeader>
          <CardContent>
            {data.pipeline_funnel.every((f) => f.count === 0) ? (
              <EmptyState text="Create applications to see funnel" />
            ) : (
              <div className="space-y-2">
                {data.pipeline_funnel.map((f, i) => {
                  const maxCount = Math.max(
                    ...data.pipeline_funnel.map((x) => x.count),
                    1
                  );
                  const colors = [
                    "bg-yellow-500",
                    "bg-blue-500",
                    "bg-purple-500",
                    "bg-orange-500",
                    "bg-green-500",
                    "bg-gray-500",
                  ];
                  return (
                    <div key={f.stage}>
                      <div className="flex justify-between text-xs mb-1">
                        <span>{f.stage}</span>
                        <span className="text-muted-foreground">{f.count}</span>
                      </div>
                      <Bar
                        value={f.count}
                        max={maxCount}
                        color={colors[i] || "bg-gray-500"}
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 10. Monthly Trends */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Monthly Trends</CardTitle>
          </CardHeader>
          <CardContent>
            {data.monthly_trends.length === 0 ? (
              <EmptyState text="No data yet" />
            ) : (
              <div className="space-y-3">
                {data.monthly_trends.map((m) => (
                  <div key={m.month} className="space-y-1">
                    <p className="text-xs font-medium">{m.month}</p>
                    <div className="grid grid-cols-3 gap-2 text-center text-xs">
                      <div>
                        <p className="font-semibold">{m.applications}</p>
                        <p className="text-muted-foreground">Apps</p>
                      </div>
                      <div>
                        <p className="font-semibold">{m.sent}</p>
                        <p className="text-muted-foreground">Sent</p>
                      </div>
                      <div>
                        <p className="font-semibold">{m.replied}</p>
                        <p className="text-muted-foreground">Replied</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
