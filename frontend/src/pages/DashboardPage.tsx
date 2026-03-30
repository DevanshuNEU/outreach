import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlusCircle, Send, MessageSquare, BarChart3, Zap, DollarSign, TrendingUp } from "lucide-react";
import { FollowUpQueueCard } from "@/components/FollowUpQueueCard";
import api from "@/lib/api";

interface Stats {
  total_applications: number;
  total_outreach: number;
  total_sent: number;
  total_replied: number;
  response_rate: number;
}

interface Usage {
  user: {
    anthropic_cost_cents: number;
    anthropic_calls: number;
    apollo_calls: number;
  };
  global: {
    apollo_total_calls: number;
    apollo_daily_limit: number;
  };
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);

  useEffect(() => {
    api.get("/api/stats").then((r) => setStats(r.data));
    api.get("/api/usage").then((r) => setUsage(r.data));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/analytics")} className="gap-2">
            <TrendingUp className="h-4 w-4" /> Analytics
          </Button>
          <Button onClick={() => navigate("/outreach/new")} className="gap-2">
            <PlusCircle className="h-4 w-4" /> New Outreach
          </Button>
        </div>
      </div>

      <FollowUpQueueCard />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> Companies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats?.total_applications ?? "-"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Send className="h-4 w-4" /> Emails Sent
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats?.total_sent ?? "-"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <MessageSquare className="h-4 w-4" /> Replies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats?.total_replied ?? "-"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="h-4 w-4" /> Response Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats?.response_rate ?? 0}%</p>
          </CardContent>
        </Card>
      </div>

      {usage && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <DollarSign className="h-4 w-4" /> API Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Anthropic Cost</p>
                <p className="text-lg font-semibold">
                  ${(usage.user.anthropic_cost_cents / 100).toFixed(4)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {usage.user.anthropic_calls} drafts
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Apollo Searches</p>
                <p className="text-lg font-semibold">{usage.user.apollo_calls}</p>
                <p className="text-xs text-muted-foreground">your searches</p>
              </div>
              <div>
                <p className="text-muted-foreground">Apollo Global</p>
                <p className="text-lg font-semibold">
                  {usage.global.apollo_total_calls} / {usage.global.apollo_daily_limit}
                </p>
                <p className="text-xs text-muted-foreground">all users today</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
