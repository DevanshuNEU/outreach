import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { Trash2 } from "lucide-react";
import api from "@/lib/api";

interface Application {
  id: string;
  company_id: string;
  job_title: string;
  email_status: string;
  status: string;
  created_at: string;
  updated_at: string;
  contact_count: number;
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

export function TrackerPage() {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<Application[]>([]);
  const [allApplications, setAllApplications] = useState<Application[]>([]);
  const [companies, setCompanies] = useState<Record<string, Company>>({});
  const [statusFilter, setStatusFilter] = useState("all");
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    const params = statusFilter !== "all" ? `?status=${statusFilter}` : "";
    const [appsRes, allAppsRes, companiesRes] = await Promise.all([
      api.get(`/api/applications${params}`),
      api.get("/api/applications"),
      api.get("/api/companies"),
    ]);
    setApplications(appsRes.data);
    setAllApplications(allAppsRes.data);
    const companyMap: Record<string, Company> = {};
    for (const c of companiesRes.data) {
      companyMap[c.id] = c;
    }
    setCompanies(companyMap);
  };

  const statusCounts = allApplications.reduce(
    (acc, app) => {
      acc[app.status] = (acc[app.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const handleStatusChange = async (appId: string, newStatus: string) => {
    await api.put(`/api/applications/${appId}`, { status: newStatus });
    const update = (apps: Application[]) =>
      apps.map((a) => (a.id === appId ? { ...a, status: newStatus } : a));
    setApplications(update);
    setAllApplications(update);
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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Tracker</h1>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-56">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">
              All ({allApplications.length})
            </SelectItem>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s}>
                {s.replace(/_/g, " ")} ({statusCounts[s] || 0})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {applications.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No applications yet. Start your first outreach!
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {applications.map((app) => {
            const company = companies[app.company_id];
            return (
              <Card
                key={app.id}
                className="cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => navigate(`/applications/${app.id}`)}
              >
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">
                        {company?.name || "Unknown"}{" "}
                        {company?.location && (
                          <span className="text-muted-foreground font-normal">
                            - {company.location}
                          </span>
                        )}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {app.job_title || "No title"}
                      </p>
                    </div>
                    <div
                      className="flex items-center gap-3"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {/* Inline status select — styled as colored badge */}
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
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(app.created_at).toLocaleDateString()}
                      </span>
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
