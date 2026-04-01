import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Search,
  Plus,
  Trash2,
  ExternalLink,
  Loader2,
  Briefcase,
  MapPin,
  Globe,
  RefreshCw,
} from "lucide-react";
import api from "@/lib/api";

// ---------- Types ----------

interface HNJob {
  company: string;
  role: string;
  location: string;
  remote: boolean;
  visa_friendly: boolean;
  tech_stack: string[];
  salary: string;
  body: string;
  hn_url: string;
  categories: string[];
}

interface TargetCompany {
  id: string;
  company_name: string;
  ats_type: "greenhouse" | "lever" | "ashby";
  ats_slug: string;
  keywords: string;
}

interface ATSJob {
  title: string;
  company_name: string;
  location: string;
  department: string;
  url: string;
}

// ---------- HN Tab ----------

function HNWhoIsHiring() {
  const navigate = useNavigate();
  const [keywords, setKeywords] = useState("");
  const [visaOnly, setVisaOnly] = useState(false);
  const [categories, setCategories] = useState<Record<string, boolean>>({
    SWE: false,
    "AI/ML": false,
    Infra: false,
  });
  const [jobs, setJobs] = useState<HNJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedIdx, setExpandedIdx] = useState<Set<number>>(new Set());

  const toggleCategory = (cat: string) => {
    setCategories((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  const search = async () => {
    setLoading(true);
    setError("");
    try {
      const activeCats = Object.entries(categories)
        .filter(([, v]) => v)
        .map(([k]) => k);
      const catMap: Record<string, string> = { SWE: "swe", "AI/ML": "ai-ml", Infra: "infra" };
      const res = await api.get("/api/jobs/hn-hiring", {
        params: {
          keywords: keywords.trim() || undefined,
          visa_only: visaOnly || undefined,
          categories: activeCats.length ? activeCats.map(c => catMap[c] || c.toLowerCase()).join(",") : undefined,
        },
      });
      setJobs(res.data.jobs || []);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to fetch HN jobs");
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (idx: number) => {
    setExpandedIdx((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px] space-y-1.5">
              <Label className="text-xs">Keywords (comma-separated)</Label>
              <Input
                placeholder="python, react, distributed systems"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && search()}
              />
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={visaOnly}
                  onChange={(e) => setVisaOnly(e.target.checked)}
                  className="rounded border-input"
                />
                Visa-friendly only
              </label>
            </div>

            <div className="flex items-center gap-3">
              {Object.keys(categories).map((cat) => (
                <label
                  key={cat}
                  className="flex items-center gap-1.5 text-sm cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={categories[cat]}
                    onChange={() => toggleCategory(cat)}
                    className="rounded border-input"
                  />
                  {cat}
                </label>
              ))}
            </div>

            <Button onClick={search} disabled={loading} className="gap-2">
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* Results */}
      {jobs.length === 0 && !loading && !error && (
        <p className="text-sm text-muted-foreground text-center py-8">
          Search the latest HN "Who is Hiring" thread above.
        </p>
      )}

      <div className="space-y-3">
        {jobs.map((job, idx) => (
          <Card key={idx}>
            <CardContent className="pt-5 pb-4 space-y-2">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold">{job.company}</span>
                    {job.remote && (
                      <Badge variant="secondary" className="text-xs">
                        <Globe className="h-3 w-3 mr-1" />
                        Remote
                      </Badge>
                    )}
                    {job.visa_friendly && (
                      <Badge className="bg-green-600 hover:bg-green-700 text-white text-xs">
                        Visa OK
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {job.role}
                    {job.location && (
                      <span className="ml-2 inline-flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {job.location}
                      </span>
                    )}
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => window.open(job.hn_url, "_blank")}
                    className="gap-1.5"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    HN
                  </Button>
                  <Button
                    size="sm"
                    onClick={() =>
                      navigate(
                        `/outreach/new?company=${encodeURIComponent(job.company)}`
                      )
                    }
                    className="gap-1.5"
                  >
                    <Briefcase className="h-3.5 w-3.5" />
                    Outreach
                  </Button>
                </div>
              </div>

              {/* Tech stack */}
              {job.tech_stack.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {job.tech_stack.map((t) => (
                    <Badge key={t} variant="outline" className="text-xs">
                      {t}
                    </Badge>
                  ))}
                </div>
              )}

              {/* Salary */}
              {job.salary && (
                <p className="text-xs text-muted-foreground">{job.salary}</p>
              )}

              {/* Body */}
              <div className="text-sm text-muted-foreground">
                {expandedIdx.has(idx) ? (
                  <p className="whitespace-pre-wrap">{job.body}</p>
                ) : (
                  <p>
                    {job.body.slice(0, 200)}
                    {job.body.length > 200 && "..."}
                  </p>
                )}
                {job.body.length > 200 && (
                  <button
                    className="text-xs underline mt-1"
                    onClick={() => toggleExpand(idx)}
                  >
                    {expandedIdx.has(idx) ? "Show less" : "Show more"}
                  </button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ---------- ATS Watcher Tab ----------

function ATSWatcher() {
  const navigate = useNavigate();
  const [targets, setTargets] = useState<TargetCompany[]>([]);
  const [atsJobs, setAtsJobs] = useState<ATSJob[]>([]);
  const [scanning, setScanning] = useState(false);
  const [, setLoadingTargets] = useState(true);
  const [error, setError] = useState("");

  // Form state
  const [companyName, setCompanyName] = useState("");
  const [atsType, setAtsType] = useState<"greenhouse" | "lever" | "ashby">(
    "greenhouse"
  );
  const [atsSlug, setAtsSlug] = useState("");
  const [atsKeywords, setAtsKeywords] = useState("");

  // Load saved targets on mount
  useEffect(() => {
    api.get("/api/jobs/targets").then((r) => {
      setTargets(r.data || []);
      setLoadingTargets(false);
    }).catch(() => setLoadingTargets(false));
  }, []);

  const addTarget = async () => {
    if (!companyName.trim() || !atsSlug.trim()) return;
    try {
      const res = await api.post("/api/jobs/targets", {
        company_name: companyName.trim(),
        ats_type: atsType,
        ats_slug: atsSlug.trim(),
        keywords: atsKeywords.trim() || undefined,
      });
      setTargets((prev) => [...prev, res.data]);
      setCompanyName("");
      setAtsSlug("");
      setAtsKeywords("");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to add target");
    }
  };

  const removeTarget = async (id: string) => {
    try {
      await api.delete(`/api/jobs/targets/${id}`);
      setTargets((prev) => prev.filter((t) => t.id !== id));
    } catch {}
  };

  const scanAll = async () => {
    if (targets.length === 0) return;
    setScanning(true);
    setError("");
    setAtsJobs([]);

    try {
      const res = await api.post("/api/jobs/scan-all");
      setAtsJobs(res.data.jobs || []);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to scan ATS boards");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Add target company form */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">
            Add Target Company
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Company Name</Label>
              <Input
                placeholder="Stripe"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">ATS Type</Label>
              <select
                value={atsType}
                onChange={(e) =>
                  setAtsType(e.target.value as "greenhouse" | "lever" | "ashby")
                }
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="greenhouse">Greenhouse</option>
                <option value="lever">Lever</option>
                <option value="ashby">Ashby</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">ATS Slug</Label>
              <Input
                placeholder="stripe"
                value={atsSlug}
                onChange={(e) => setAtsSlug(e.target.value)}
              />
              <p className="text-[11px] text-muted-foreground">
                e.g. "stripe" from boards.greenhouse.io/stripe
              </p>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Keywords (optional)</Label>
              <Input
                placeholder="backend, python"
                value={atsKeywords}
                onChange={(e) => setAtsKeywords(e.target.value)}
              />
            </div>
          </div>
          <Button
            size="sm"
            onClick={addTarget}
            disabled={!companyName.trim() || !atsSlug.trim()}
            className="gap-1.5"
          >
            <Plus className="h-4 w-4" />
            Add
          </Button>
        </CardContent>
      </Card>

      {/* Target company list */}
      {targets.length > 0 && (
        <Card>
          <CardContent className="pt-5">
            <div className="space-y-2">
              {targets.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between py-2 px-3 rounded-md bg-muted/50"
                >
                  <div className="text-sm">
                    <span className="font-medium">{t.company_name}</span>
                    <span className="text-muted-foreground ml-2">
                      {t.ats_type}/{t.ats_slug}
                    </span>
                    {t.keywords && (
                      <span className="text-muted-foreground ml-2 text-xs">
                        [{t.keywords}]
                      </span>
                    )}
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => removeTarget(t.id)}
                    className="h-7 w-7"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
            <Button
              onClick={scanAll}
              disabled={scanning}
              className="mt-3 gap-2"
            >
              {scanning ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Scan All
            </Button>
          </CardContent>
        </Card>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* ATS job results */}
      {atsJobs.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-muted-foreground">
            {atsJobs.length} matching job{atsJobs.length !== 1 && "s"} found
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {atsJobs.map((job, idx) => (
              <Card key={idx}>
                <CardContent className="pt-5 pb-4 space-y-2">
                  <div>
                    <p className="font-medium text-sm">{job.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {job.company_name}
                      {job.department && ` / ${job.department}`}
                    </p>
                  </div>
                  {job.location && (
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {job.location}
                    </p>
                  )}
                  <div className="flex gap-2 pt-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => window.open(job.url, "_blank")}
                      className="gap-1.5"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Apply
                    </Button>
                    <Button
                      size="sm"
                      onClick={() =>
                        navigate(
                          `/outreach/new?company=${encodeURIComponent(job.company_name)}&jobTitle=${encodeURIComponent(job.title)}`
                        )
                      }
                      className="gap-1.5"
                    >
                      <Briefcase className="h-3.5 w-3.5" />
                      Outreach
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {atsJobs.length === 0 && !scanning && !error && targets.length > 0 && (
        <p className="text-sm text-muted-foreground text-center py-6">
          Hit "Scan All" to check your target companies for open roles.
        </p>
      )}

      {targets.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          Add target companies above to watch their job boards.
        </p>
      )}
    </div>
  );
}

// ---------- Main Page ----------

export function JobFinderPage() {
  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Job Finder</h1>
        <p className="text-muted-foreground mt-1">
          Find roles from HN threads and company job boards.
        </p>
      </div>

      <Tabs defaultValue="hn">
        <TabsList>
          <TabsTrigger value="hn">HN Who is Hiring</TabsTrigger>
          <TabsTrigger value="ats">ATS Watcher</TabsTrigger>
        </TabsList>

        <TabsContent value="hn">
          <HNWhoIsHiring />
        </TabsContent>

        <TabsContent value="ats">
          <ATSWatcher />
        </TabsContent>
      </Tabs>
    </div>
  );
}
