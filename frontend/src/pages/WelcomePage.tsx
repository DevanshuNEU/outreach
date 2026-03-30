import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import {
  Loader2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Mail,
  Users,
  BarChart3,
  CheckCircle,
  Clock,
  Send,
  Target,
} from "lucide-react";
import api from "@/lib/api";

interface Props {
  username: string;
  onComplete: () => void;
}

type Step = 1 | 2 | 3 | 4 | 5;

interface Project {
  name: string;
  description: string;
  metrics: string;
  url: string;
}

export function WelcomePage({ username, onComplete }: Props) {
  const [step, setStep] = useState<Step>(1);

  // Profile form
  const [fullName, setFullName] = useState("");
  const [background, setBackground] = useState("");
  const [signOff, setSignOff] = useState(`Best,\n${username}`);
  const [linksBlock, setLinksBlock] = useState("");
  const [projects, setProjects] = useState<Project[]>([
    { name: "", description: "", metrics: "", url: "" },
  ]);
  const [savingProfile, setSavingProfile] = useState(false);

  // Templates
  const [templates, setTemplates] = useState<any[]>([]);
  const [generatingTemplates, setGeneratingTemplates] = useState(false);

  const saveProfile = async () => {
    setSavingProfile(true);
    try {
      const validProjects = projects.filter((p) => p.name.trim());
      await api.put("/api/profile", {
        full_name: fullName,
        background,
        sign_off_block: signOff,
        links_block: linksBlock,
        projects: validProjects,
      });
      setStep(3);
    } catch {
      alert("Failed to save profile. Check your fields.");
    } finally {
      setSavingProfile(false);
    }
  };

  const generateTemplates = async () => {
    setGeneratingTemplates(true);
    try {
      const res = await api.post("/api/templates/generate");
      setTemplates(res.data);
    } catch {
      alert("Failed to generate. Make sure your profile background is filled in.");
    } finally {
      setGeneratingTemplates(false);
    }
  };

  const addProject = () => {
    setProjects([...projects, { name: "", description: "", metrics: "", url: "" }]);
  };

  const updateProject = (i: number, field: keyof Project, val: string) => {
    const updated = [...projects];
    updated[i] = { ...updated[i], [field]: val };
    setProjects(updated);
  };

  const removeProject = (i: number) => {
    setProjects(projects.filter((_, idx) => idx !== i));
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Progress bar */}
      <div className="w-full h-1 bg-gray-100 dark:bg-gray-800">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${(step / 5) * 100}%` }}
        />
      </div>

      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl space-y-6">
          {/* Step indicator */}
          <div className="flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map((s) => (
              <div
                key={s}
                className={`h-2 w-2 rounded-full transition-colors ${
                  s <= step ? "bg-primary" : "bg-gray-200 dark:bg-gray-700"
                }`}
              />
            ))}
          </div>

          {/* ─── Step 1: Welcome ─── */}
          {step === 1 && (
            <div className="text-center space-y-6">
              <div>
                <h1 className="text-3xl font-bold">Hey {username}!</h1>
                <p className="text-muted-foreground mt-2 text-lg">
                  Let's get you set up in 3 minutes.
                </p>
              </div>

              <div className="grid gap-4 text-left max-w-md mx-auto">
                <div className="flex gap-3 items-start">
                  <Mail className="h-5 w-5 text-blue-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium">AI drafts your cold emails</p>
                    <p className="text-sm text-muted-foreground">
                      Paste a JD, pick a template. 120-word personalized email in seconds.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3 items-start">
                  <Users className="h-5 w-5 text-green-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium">Find the right contacts</p>
                    <p className="text-sm text-muted-foreground">
                      Apollo finds hiring managers and recruiters with verified emails.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3 items-start">
                  <BarChart3 className="h-5 w-5 text-purple-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium">Track what works</p>
                    <p className="text-sm text-muted-foreground">
                      Follow-up reminders, reply tracking, and analytics to sharpen your strategy.
                    </p>
                  </div>
                </div>
              </div>

              <Button size="lg" onClick={() => setStep(2)} className="gap-2">
                Let's go <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* ─── Step 2: Profile ─── */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">Your Profile</h2>
                <p className="text-muted-foreground">
                  This powers every email the AI writes for you. Be specific about your wins.
                </p>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Devanshu Chicholikar"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Background</Label>
                  <Textarea
                    value={background}
                    onChange={(e) => setBackground(e.target.value)}
                    placeholder="MS Software Engineering @ Northeastern, GPA 3.85, graduating May 2026. Built production systems that handle 10K+ requests/sec. Open source contributor. F1/OPT, 3 years work auth."
                    rows={4}
                  />
                  <p className="text-xs text-muted-foreground">
                    Include: degree, GPA, key achievements with numbers, work authorization status
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Links Block (appended to every email)</Label>
                  <Textarea
                    value={linksBlock}
                    onChange={(e) => setLinksBlock(e.target.value)}
                    placeholder={"Portfolio: https://yoursite.com\nGitHub: https://github.com/you\nLinkedIn: https://linkedin.com/in/you"}
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Sign-off</Label>
                  <Textarea
                    value={signOff}
                    onChange={(e) => setSignOff(e.target.value)}
                    rows={2}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Projects (your proof points)</Label>
                    <Button variant="outline" size="sm" onClick={addProject}>
                      + Add Project
                    </Button>
                  </div>
                  {projects.map((p, i) => (
                    <Card key={i}>
                      <CardContent className="pt-4 space-y-2">
                        <div className="flex gap-2">
                          <Input
                            placeholder="Project name"
                            value={p.name}
                            onChange={(e) => updateProject(i, "name", e.target.value)}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-muted-foreground"
                            onClick={() => removeProject(i)}
                          >
                            Remove
                          </Button>
                        </div>
                        <Input
                          placeholder="One-line description"
                          value={p.description}
                          onChange={(e) => updateProject(i, "description", e.target.value)}
                        />
                        <Input
                          placeholder="Key metrics (e.g. 87.5% Hit@1, p95 800ms → 280ms)"
                          value={p.metrics}
                          onChange={(e) => updateProject(i, "metrics", e.target.value)}
                        />
                        <Input
                          placeholder="URL (optional)"
                          value={p.url}
                          onChange={(e) => updateProject(i, "url", e.target.value)}
                        />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(1)}>
                  <ArrowLeft className="h-4 w-4 mr-1" /> Back
                </Button>
                <Button
                  onClick={saveProfile}
                  disabled={savingProfile || !fullName.trim() || !background.trim()}
                  className="flex-1 gap-2"
                >
                  {savingProfile ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Saving...
                    </>
                  ) : (
                    <>
                      Save & Continue <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* ─── Step 3: Templates ─── */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">Role Templates</h2>
                <p className="text-muted-foreground">
                  Templates shape how the AI writes for different roles. We'll generate them from your profile.
                </p>
              </div>

              {templates.length === 0 ? (
                <div className="text-center py-8 space-y-4">
                  <Sparkles className="h-12 w-12 text-muted-foreground mx-auto" />
                  <p className="text-muted-foreground">
                    One click and we'll create role-specific templates based on your background.
                  </p>
                  <Button
                    onClick={generateTemplates}
                    disabled={generatingTemplates}
                    size="lg"
                    className="gap-2"
                  >
                    {generatingTemplates ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" /> Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" /> Generate from Profile
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2">
                  {templates.map((t: any) => (
                    <Card key={t.id}>
                      <CardContent className="pt-4">
                        <div className="flex items-center gap-2">
                          <div
                            className="h-3 w-3 rounded-full"
                            style={{ backgroundColor: t.color }}
                          />
                          <span className="font-medium text-sm">{t.title}</span>
                        </div>
                        {t.tagline && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {t.tagline}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(2)}>
                  <ArrowLeft className="h-4 w-4 mr-1" /> Back
                </Button>
                <Button onClick={() => setStep(4)} className="flex-1 gap-2">
                  Continue <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* ─── Step 4: First Outreach ─── */}
          {step === 4 && (
            <div className="text-center space-y-6">
              <div>
                <h2 className="text-2xl font-bold">Ready to reach out?</h2>
                <p className="text-muted-foreground">
                  You can start your first outreach now or explore the platform first.
                </p>
              </div>

              <div className="flex flex-col gap-3 max-w-sm mx-auto">
                <Button
                  size="lg"
                  className="gap-2"
                  onClick={() => {
                    onComplete();
                    window.location.href = "/outreach/new";
                  }}
                >
                  <Send className="h-4 w-4" /> Start First Outreach
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => setStep(5)}
                >
                  I'll explore first
                </Button>
              </div>
            </div>
          )}

          {/* ─── Step 5: Workflow Summary ─── */}
          {step === 5 && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold">You're all set!</h2>
                <p className="text-muted-foreground">
                  Here's your Mon-Thu cold outreach workflow.
                </p>
              </div>

              <div className="space-y-4 max-w-md mx-auto">
                <div className="flex gap-3 items-start">
                  <div className="h-8 w-8 rounded-full bg-orange-100 flex items-center justify-center shrink-0">
                    <Clock className="h-4 w-4 text-orange-600" />
                  </div>
                  <div>
                    <p className="font-medium">Morning: Check follow-ups</p>
                    <p className="text-sm text-muted-foreground">
                      Dashboard shows which contacts need follow-up today. One click to mark sent.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3 items-start">
                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                    <Target className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium">Find jobs, start outreach</p>
                    <p className="text-sm text-muted-foreground">
                      Paste a JD, pick template, AI drafts email, Apollo finds contacts. Copy and send.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3 items-start">
                  <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center shrink-0">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium">Track everything</p>
                    <p className="text-sm text-muted-foreground">
                      Mark emails sent, log replies. Follow-ups auto-scheduled: Day 3, 10, 17.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3 items-start">
                  <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center shrink-0">
                    <BarChart3 className="h-4 w-4 text-purple-600" />
                  </div>
                  <div>
                    <p className="font-medium">Weekly: Check analytics</p>
                    <p className="text-sm text-muted-foreground">
                      Which templates get replies? What company size responds most? Data drives strategy.
                    </p>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <Button size="lg" onClick={onComplete} className="gap-2">
                  Go to Dashboard <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
