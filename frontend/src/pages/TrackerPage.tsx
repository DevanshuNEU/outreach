import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Trash2, ArrowUpDown } from "lucide-react";
import api from "@/lib/api";

interface NextFollowUp {
  followup_number: number;
  due_date: string;
  is_overdue: boolean;
}

interface Application {
  id: string;
  company_id: string;
  job_title: string;
  email_status: string;
  status: string;
  created_at: string;
  updated_at: string;
  contact_count: number;
  next_followup: NextFollowUp | null;
  has_reply: boolean;
}

interface Company {
  id: string;
  name: string;
  location: string;
}

const STATUS_COLORS: Record<string, string> = {
  drafting: "bg-yellow-100 text-yellow-800",
  ready: "bg-blue-100 text-blue-800",
  outreach_in_progress: "bg-purple-100 text-purple-800",
  waiting: "bg-orange-100 text-orange-800",
  replied: "bg-green-100 text-green-800",
  closed: "bg-gray-100 text-gray-800",
};

const STATUSES = [
  "drafting",
  "ready",
  "outreach_in_progress",
  "waiting",
  "replied",
  "closed",
];

type SortOption = "newest" | "oldest" | "followup_due" | "replied_first";
type FilterOption = "all" | "needs_followup" | "has_reply" | "no_reply" | string;

function daysAgo(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
  if (diff === 0) return "today";
  if (diff === 1) return "1 day ago";
  return `${diff} days ago`;
}

function followUpBadge(app: Application) {
  if (app.has_reply) {
    return <Badge className="bg-green-100 text-green-800 text-[10px] px-1.5">Replied</Badge>;
  }
  if (!app.next_followup) return null;
  const fu = app.next_followup;
  if (fu.is_overdue) {
    return (
      <Badge className="bg-red-100 text-red-800 text-[10px] px-1.5 animate-pulse">
        FU{fu.followup_number} overdue
      </Badge>
    );
  }
  const daysUntil = Math.ceil(
    (new Date(fu.due_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );
  if (daysUntil <= 0) {
    return (
      <Badge className="bg-orange-100 text-orange-800 text-[10px] px-1.5">
        FU{fu.followup_number} due today
      </Badge>
    );
  }
  if (daysUntil <= 3) {
    return (
      <Badge className="bg-yellow-100 text-yellow-800 text-[10px] px-1.5">
        FU{fu.followup_number} in {daysUntil}d
      </Badge>
    );
  }
  return (
    <Badge className="bg-gray-100 text-gray-600 text-[10px] px-1.5">
      FU{fu.followup_number} in {daysUntil}d
    </Badge>
  );
}

export function TrackerPage() {
  const navigate = useNavigate();
  const [allApplications, setAllApplications] = useState<Application[]>([]);
  const [companies, setCompanies] = useState<Record<string, Company>>({});
  const [statusFilter, setStatusFilter] = useState<FilterOption>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const [appsRes, companiesRes] = await Promise.all([
      api.get("/api/applications"),
      api.get("/api/companies"),
    ]);
    setAllApplications(appsRes.data);
    const companyMap: Record<string, Company> = {};
    for (const c of companiesRes.data) {
      companyMap[c.id] = c;
    }
    setCompanies(companyMap);
  };

  // Filter
  const filtered = allApplications.filter((app) => {
    if (statusFilter === "all") return true;
    if (statusFilter === "needs_followup")
      return app.next_followup && !app.has_reply;
    if (statusFilter === "has_reply") return app.has_reply;
    if (statusFilter === "no_reply")
      return !app.has_reply && !app.next_followup && app.contact_count > 0;
    return app.status === statusFilter;
  });

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    switch (sortBy) {
      case "oldest":
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      case "followup_due": {
        const aDate = a.next_followup?.due_date ?? "9999-12-31";
        const bDate = b.next_followup?.due_date ?? "9999-12-31";
        return new Date(aDate).getTime() - new Date(bDate).getTime();
      }
      case "replied_first":
        return (b.has_reply ? 1 : 0) - (a.has_reply ? 1 : 0);
      default: // newest
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }
  });

  const statusCounts = allApplications.reduce(
    (acc, app) => {
      acc[app.status] = (acc[app.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const needsFollowUpCount = allApplications.filter(
    (a) => a.next_followup && !a.has_reply
  ).length;
  const hasReplyCount = allApplications.filter((a) => a.has_reply).length;

  const handleStatusChange = async (appId: string, newStatus: string) => {
    await api.put(`/api/applications/${appId}`, { status: newStatus });
    setAllApplications((apps) =>
      apps.map((a) => (a.id === appId ? { ...a, status: newStatus } : a))
    );
  };

  const handleDelete = async () => {
    if (!deleteTargetId) return;
    await api.delete(`/api/outreach?application_id=${deleteTargetId}`);
    await api.delete(`/api/applications/${deleteTargetId}`);
    setDeleteTargetId(null);
    await loadData();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">Tracker</h1>
        <div className="flex items-center gap-2">
          {/* Sort */}
          <Select value={sortBy} onValueChange={(v) => setSortBy(v as SortOption)}>
            <SelectTrigger className="w-44">
              <ArrowUpDown className="h-3 w-3 mr-1" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest first</SelectItem>
              <SelectItem value="oldest">Oldest first</SelectItem>
              <SelectItem value="followup_due">Follow-up due soonest</SelectItem>
              <SelectItem value="replied_first">Replied first</SelectItem>
            </SelectContent>
          </Select>

          {/* Filter */}
          <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "all")}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="Filter" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All ({allApplications.length})</SelectItem>
              <SelectItem value="needs_followup">
                Needs Follow-Up ({needsFollowUpCount})
              </SelectItem>
              <SelectItem value="has_reply">Replied ({hasReplyCount})</SelectItem>
              <SelectItem value="no_reply">No Reply Yet</SelectItem>
              {STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {s.replace(/_/g, " ")} ({statusCounts[s] || 0})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {sorted.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            {allApplications.length === 0
              ? "No applications yet. Start your first outreach!"
              : "No applications match this filter."}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {sorted.map((app) => {
            const company = companies[app.company_id];
            return (
              <Card
                key={app.id}
                className="cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => navigate(`/applications/${app.id}`)}
              >
                <CardContent className="py-4">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium truncate">
                          {company?.name || "Unknown"}
                        </p>
                        {company?.location && (
                          <span className="text-xs text-muted-foreground">
                            {company.location}
                          </span>
                        )}
                        {followUpBadge(app)}
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                        <span>{app.job_title || "No title"}</span>
                        <span className="text-xs">
                          {daysAgo(app.created_at)}
                        </span>
                      </div>
                    </div>
                    <div
                      className="flex items-center gap-2 shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <select
                        value={app.status}
                        onChange={(e) =>
                          handleStatusChange(app.id, e.target.value)
                        }
                        className={`text-xs font-medium rounded-full px-2.5 py-0.5 border-0 cursor-pointer appearance-none focus:outline-none ${STATUS_COLORS[app.status] || ""}`}
                      >
                        {STATUSES.map((s) => (
                          <option key={s} value={s}>
                            {s.replace(/_/g, " ")}
                          </option>
                        ))}
                      </select>

                      {app.contact_count > 0 && (
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {app.contact_count} contact
                          {app.contact_count !== 1 ? "s" : ""}
                        </span>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground hover:text-destructive"
                        onClick={() => setDeleteTargetId(app.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Dialog
        open={!!deleteTargetId}
        onOpenChange={(open: boolean) => !open && setDeleteTargetId(null)}
      >
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>Delete this application?</DialogTitle>
            <DialogDescription>
              This permanently deletes the application and all outreach records
              linked to it. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTargetId(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
