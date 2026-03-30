import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Loader2, ArrowRight, CheckCircle, XCircle, AlertCircle, Zap } from "lucide-react";
import api from "@/lib/api";

interface FitResult {
  fit_score: number;
  verdict: "Strong Yes" | "Yes" | "Borderline" | "No";
  verdict_reason: string;
  strengths: string[];
  gaps: string[];
  talking_points: string[];
  company_name: string | null;
  job_title: string | null;
  extracted_jd: string;
}

export function FitAnalyzerPage() {
  const navigate = useNavigate();
  const [jobUrl, setJobUrl] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FitResult | null>(null);
  const [error, setError] = useState("");
  const [showPaste, setShowPaste] = useState(false);

  const analyze = async () => {
    if (!jobUrl.trim() && !jobDescription.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.post("/api/analyze-fit", {
        job_url: jobUrl.trim() || undefined,
        job_description: jobDescription.trim() || undefined,
      });
      setResult(res.data);
    } catch (e: any) {
      const msg = e.response?.data?.detail || "Failed to analyze. Try pasting the JD directly.";
      setError(msg);
      setShowPaste(true);
    } finally {
      setLoading(false);
    }
  };

  const startOutreach = () => {
    if (!result) return;
    const params = new URLSearchParams();
    if (result.company_name) params.set("company", result.company_name);
    if (result.job_title) params.set("jobTitle", result.job_title);
    params.set("jd", result.extracted_jd.slice(0, 2000));
    navigate(`/outreach/new?${params.toString()}`);
  };

  const verdictConfig = {
    "Strong Yes": { color: "bg-green-500", icon: CheckCircle, text: "text-green-600", badge: "bg-green-100 text-green-800" },
    "Yes": { color: "bg-green-400", icon: CheckCircle, text: "text-green-600", badge: "bg-green-100 text-green-700" },
    "Borderline": { color: "bg-yellow-400", icon: AlertCircle, text: "text-yellow-600", badge: "bg-yellow-100 text-yellow-800" },
    "No": { color: "bg-red-400", icon: XCircle, text: "text-red-600", badge: "bg-red-100 text-red-800" },
  };

  const config = result ? verdictConfig[result.verdict] : null;

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Job Fit Analyzer</h1>
        <p className="text-muted-foreground mt-1">
          Paste a job link. Get a straight answer on whether to reach out.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="space-y-2">
            <Label>Job Posting URL</Label>
            <Input
              placeholder="https://jobs.ashbyhq.com/company/role or LinkedIn, Greenhouse, Lever..."
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && analyze()}
            />
          </div>

          {(showPaste || !jobUrl.trim()) && (
            <div className="space-y-2">
              <Label className="text-muted-foreground text-sm">
                Or paste the JD directly (if URL doesn't work)
              </Label>
              <Textarea
                placeholder="Paste the full job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={6}
                className="text-sm"
              />
            </div>
          )}

          {!showPaste && jobUrl.trim() && (
            <button
              className="text-xs text-muted-foreground underline"
              onClick={() => setShowPaste(true)}
            >
              URL not working? Paste JD instead
            </button>
          )}

          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}

          <Button
            onClick={analyze}
            disabled={loading || (!jobUrl.trim() && !jobDescription.trim())}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Zap className="mr-2 h-4 w-4" />
                Analyze Fit
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {result && config && (
        <div className="space-y-4 animate-in fade-in duration-300">
          {/* Score card */}
          <Card className="overflow-hidden">
            <div className={`h-2 ${config.color}`} />
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-4xl font-bold">{result.fit_score}</span>
                    <span className="text-muted-foreground text-lg">/10</span>
                    <Badge className={`ml-2 ${config.badge} border-0 font-medium`}>
                      {result.verdict}
                    </Badge>
                  </div>
                  {(result.company_name || result.job_title) && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {[result.job_title, result.company_name].filter(Boolean).join(" at ")}
                    </p>
                  )}
                </div>
                {(result.verdict === "Strong Yes" || result.verdict === "Yes") && (
                  <Button onClick={startOutreach} className="gap-2">
                    Start Outreach
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <p className={`mt-3 text-sm font-medium ${config.text}`}>
                {result.verdict_reason}
              </p>
            </CardContent>
          </Card>

          {/* Strengths */}
          {result.strengths.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-green-700 flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" />
                  Why you fit
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {result.strengths.map((s, i) => (
                  <div key={i} className="flex gap-2 text-sm">
                    <span className="text-green-500 mt-0.5 shrink-0">✓</span>
                    <span>{s}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Gaps */}
          {result.gaps.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-orange-700 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Honest gaps
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {result.gaps.map((g, i) => (
                  <div key={i} className="flex gap-2 text-sm">
                    <span className="text-orange-400 mt-0.5 shrink-0">△</span>
                    <span>{g}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Talking points */}
          {result.talking_points.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Zap className="h-4 w-4 text-blue-500" />
                  Lead with these in your cold email
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {result.talking_points.map((t, i) => (
                  <div key={i} className="flex gap-2 text-sm">
                    <span className="text-blue-400 mt-0.5 shrink-0">→</span>
                    <span>{t}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <Separator />

          {result.verdict === "Borderline" || result.verdict === "No" ? (
            <p className="text-sm text-muted-foreground text-center">
              Not the right fit? Move on fast.{" "}
              <button className="underline" onClick={() => { setResult(null); setJobUrl(""); setJobDescription(""); setShowPaste(false); }}>
                Analyze another role
              </button>
            </p>
          ) : (
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => { setResult(null); setJobUrl(""); setJobDescription(""); setShowPaste(false); }}>
                Analyze Another
              </Button>
              <Button className="flex-1 gap-2" onClick={startOutreach}>
                Start Outreach <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
