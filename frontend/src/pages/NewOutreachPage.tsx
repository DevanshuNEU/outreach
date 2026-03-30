import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { CopyButton } from "@/components/CopyButton";
import {
  ArrowRight,
  ArrowLeft,
  Loader2,
  Mail,
  Users,
  Check,
  RefreshCw,
  Plus,
  UserPlus,
  Link,
} from "lucide-react";
import api from "@/lib/api";

interface Template {
  id: string;
  slug: string;
  title: string;
  color: string;
  tagline: string;
}

interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  title: string;
  seniority: string;
  email: string;
  linkedin_url: string;
}

type Step = "input" | "template" | "draft" | "contacts" | "send";

export function NewOutreachPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("input");

  // Step 1: Input
  const [companyName, setCompanyName] = useState("");
  const [location, setLocation] = useState("");
  const [domain, setDomain] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");

  // Step 2: Template
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");

  // Step 3: Draft
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [linkedinNote, setLinkedinNote] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [wordCount, setWordCount] = useState(0);

  // Step 4: Contacts
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [findingContacts, setFindingContacts] = useState(false);
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualFirst, setManualFirst] = useState("");
  const [manualLast, setManualLast] = useState("");
  const [manualTitle, setManualTitle] = useState("");
  const [manualEmail, setManualEmail] = useState("");
  const [manualLinkedin, setManualLinkedin] = useState("");
  const [addingManual, setAddingManual] = useState(false);

  // Apollo credits
  const [apolloCredits, setApolloCredits] = useState<{
    daily_used: number;
    daily_limit: number;
    daily_remaining: number;
    monthly_used: number;
    monthly_total: number;
  } | null>(null);

  // IDs
  const [companyId, setCompanyId] = useState("");
  const [applicationId, setApplicationId] = useState("");

  // Profile data for email assembly
  const [signOff, setSignOff] = useState("");
  const [linksBlock, setLinksBlock] = useState("");

  useEffect(() => {
    api.get("/api/templates").then((r) => setTemplates(r.data));
    api.get("/api/profile").then((r) => {
      setSignOff(r.data.sign_off_block || "");
      setLinksBlock(r.data.links_block || "");
    });
  }, []);

  useEffect(() => {
    if (step === "contacts") {
      api.get("/api/apollo/credits").then((r) => setApolloCredits(r.data)).catch(() => {});
    }
  }, [step]);

  useEffect(() => {
    const words = emailBody.trim().split(/\s+/).filter(Boolean).length;
    setWordCount(words);
  }, [emailBody]);

  const handleCreateApplication = async () => {
    // Create or find company
    const companyRes = await api.post("/api/companies", {
      name: companyName,
      domain: domain || undefined,
      location: location || undefined,
    });
    const cId = companyRes.data.id;
    setCompanyId(cId);

    // Create application
    const appRes = await api.post("/api/applications", {
      company_id: cId,
      job_title: jobTitle || undefined,
      job_description: jobDescription || undefined,
    });
    setApplicationId(appRes.data.id);
    setStep("template");
  };

  const handleDraftEmail = async () => {
    setDrafting(true);
    try {
      const res = await api.post(
        `/api/applications/${applicationId}/draft-email`,
        { role_template_id: selectedTemplate }
      );
      setEmailSubject(res.data.subject);
      setEmailBody(res.data.body);
      setLinkedinNote(res.data.linkedin_note || "");
      setStep("draft");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Draft failed");
    } finally {
      setDrafting(false);
    }
  };

  const handleConfirmDraft = async () => {
    await api.put(`/api/applications/${applicationId}`, {
      email_subject: emailSubject,
      email_body: emailBody,
      email_status: "confirmed",
      status: "ready",
      role_template_id: selectedTemplate,
      linkedin_note: linkedinNote || undefined,
    });
    setStep("contacts");
  };

  const handleFindContacts = async () => {
    setFindingContacts(true);
    try {
      const res = await api.post(
        `/api/applications/${applicationId}/find-contacts`
      );
      setContacts(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to find contacts");
    } finally {
      setFindingContacts(false);
    }
  };

  const handleAddManualContact = async () => {
    if (!manualFirst || !manualEmail) return;
    setAddingManual(true);
    try {
      const res = await api.post("/api/contacts/manual", {
        company_id: companyId,
        first_name: manualFirst,
        last_name: manualLast,
        title: manualTitle || undefined,
        email: manualEmail,
        linkedin_url: manualLinkedin || undefined,
      });
      setContacts((prev) => [...prev, res.data]);
      setManualFirst(""); setManualLast(""); setManualTitle("");
      setManualEmail(""); setManualLinkedin("");
      setShowManualForm(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to add contact");
    } finally {
      setAddingManual(false);
    }
  };

  const handleAddToOutreach = async (contact: Contact) => {
    await api.post("/api/outreach", {
      application_id: applicationId,
      contact_id: contact.id,
    });
    setStep("send");
  };

  const handleAddAllToOutreach = async () => {
    for (const c of contacts) {
      await api.post("/api/outreach", {
        application_id: applicationId,
        contact_id: c.id,
      });
    }
    await api.put(`/api/applications/${applicationId}`, {
      status: "outreach_in_progress",
    });
    navigate(`/applications/${applicationId}`);
  };

  const buildFullEmail = (firstName: string) => {
    return `Hey ${firstName},\n\n${emailBody}\n\n${linksBlock}\n\n${signOff}`;
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">New Outreach</h1>

      {/* Progress */}
      <div className="flex items-center gap-2 text-sm">
        {(["input", "template", "draft", "contacts", "send"] as Step[]).map(
          (s, i) => (
            <div key={s} className="flex items-center gap-2">
              {i > 0 && <ArrowRight className="h-3 w-3 text-muted-foreground" />}
              <Badge variant={step === s ? "default" : "outline"}>
                {s === "input" && "Company"}
                {s === "template" && "Template"}
                {s === "draft" && "Email"}
                {s === "contacts" && "Contacts"}
                {s === "send" && "Send"}
              </Badge>
            </div>
          )
        )}
      </div>

      {/* Step 1: Company Input */}
      {step === "input" && (
        <Card>
          <CardHeader>
            <CardTitle>Company & Job Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Company Name *</Label>
                <Input
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Stripe"
                />
              </div>
              <div className="space-y-2">
                <Label>Location</Label>
                <Input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="San Francisco, CA"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Domain (optional)</Label>
                <Input
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  placeholder="stripe.com"
                />
              </div>
              <div className="space-y-2">
                <Label>Job Title</Label>
                <Input
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="Senior AI Engineer"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Job Description (paste full JD)</Label>
              <Textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the full job description here..."
                rows={8}
              />
            </div>
            <Button
              onClick={handleCreateApplication}
              disabled={!companyName}
              className="gap-2"
            >
              Next <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Template Selection */}
      {step === "template" && (
        <Card>
          <CardHeader>
            <CardTitle>Select Role Template</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTemplate(t.id)}
                  className={`p-4 rounded-lg border text-left transition-all ${
                    selectedTemplate === t.id
                      ? "border-primary bg-primary/5 ring-2 ring-primary/20"
                      : "border-border hover:border-primary/50"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ background: t.color }}
                    />
                    <span className="font-medium text-sm">{t.title}</span>
                  </div>
                  {t.tagline && (
                    <p className="text-xs text-muted-foreground">{t.tagline}</p>
                  )}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep("input")}>
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
              </Button>
              <Button
                onClick={handleDraftEmail}
                disabled={!selectedTemplate || drafting}
                className="gap-2"
              >
                {drafting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Mail className="h-4 w-4" />
                )}
                Generate Draft
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Email Draft */}
      {step === "draft" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Email Draft</span>
              <div className="flex items-center gap-2">
                <Badge variant={wordCount > 130 ? "destructive" : "secondary"}>
                  {wordCount} words
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDraftEmail}
                  disabled={drafting}
                >
                  <RefreshCw className={`h-3 w-3 mr-1 ${drafting ? "animate-spin" : ""}`} />
                  Regenerate
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Subject Line</Label>
              <Input
                value={emailSubject}
                onChange={(e) => setEmailSubject(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Body (greeting added per contact)</Label>
              <Textarea
                value={emailBody}
                onChange={(e) => setEmailBody(e.target.value)}
                rows={12}
                className="font-mono text-sm"
              />
            </div>
            {linkedinNote && (
              <>
                <Separator />
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Link className="h-3.5 w-3.5 text-blue-500" />
                      LinkedIn Connection Note ({linkedinNote.length}/300 chars)
                    </Label>
                    <CopyButton text={linkedinNote} label="Copy Note" />
                  </div>
                  <p className="text-sm bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-3 text-blue-900 dark:text-blue-100">
                    {linkedinNote}
                  </p>
                </div>
              </>
            )}
            <Separator />
            <div className="text-sm text-muted-foreground space-y-1">
              <p className="font-medium">Preview sign-off:</p>
              <pre className="whitespace-pre-wrap">{linksBlock}</pre>
              <pre className="whitespace-pre-wrap">{signOff}</pre>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep("template")}>
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
              </Button>
              <Button onClick={handleConfirmDraft} className="gap-2">
                <Check className="h-4 w-4" /> Confirm Draft
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Find Contacts */}
      {step === "contacts" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Contacts at {companyName}</span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowManualForm((v) => !v)}
                  className="gap-1"
                >
                  <UserPlus className="h-3.5 w-3.5" />
                  Add Manually
                </Button>
                <Button
                  onClick={handleFindContacts}
                  disabled={findingContacts || apolloCredits?.daily_remaining === 0}
                  size="sm"
                  className="gap-2"
                >
                  {findingContacts ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Users className="h-4 w-4" />
                  )}
                  Search Apollo
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">

            {/* Apollo credit usage */}
            {apolloCredits && (
              <p className={`text-xs ${apolloCredits.daily_remaining === 0 ? "text-destructive font-medium" : "text-muted-foreground"}`}>
                Apollo today: {apolloCredits.daily_used}/{apolloCredits.daily_limit} credits
                {" · "}Month: {apolloCredits.monthly_used}/{apolloCredits.monthly_total}
                {apolloCredits.daily_remaining === 0 && " — daily limit reached, try again tomorrow"}
              </p>
            )}

            {/* Manual add form */}
            {showManualForm && (
              <div className="p-4 rounded-lg border border-dashed space-y-3">
                <p className="text-sm font-medium">Add contact manually (from LinkedIn)</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">First Name *</Label>
                    <Input value={manualFirst} onChange={(e) => setManualFirst(e.target.value)} placeholder="Jane" />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Last Name</Label>
                    <Input value={manualLast} onChange={(e) => setManualLast(e.target.value)} placeholder="Smith" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Title</Label>
                    <Input value={manualTitle} onChange={(e) => setManualTitle(e.target.value)} placeholder="Engineering Manager" />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Email *</Label>
                    <Input value={manualEmail} onChange={(e) => setManualEmail(e.target.value)} placeholder="jane@company.com" type="email" />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">LinkedIn URL (optional)</Label>
                  <Input value={manualLinkedin} onChange={(e) => setManualLinkedin(e.target.value)} placeholder="https://linkedin.com/in/janesmith" />
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleAddManualContact}
                    disabled={!manualFirst || !manualEmail || addingManual}
                    className="gap-1"
                  >
                    {addingManual ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
                    Add Contact
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowManualForm(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {contacts.length === 0 && !findingContacts && !showManualForm && (
              <p className="text-muted-foreground text-sm">
                Search Apollo for auto-discovery, or add contacts manually from LinkedIn.
              </p>
            )}

            {contacts.length > 0 && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  {contacts.length} contact{contacts.length > 1 ? "s" : ""} added
                </p>
                {contacts.map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center justify-between p-3 rounded-lg border"
                  >
                    <div>
                      <p className="font-medium">
                        {c.first_name} {c.last_name}
                      </p>
                      <p className="text-sm text-muted-foreground">{c.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        {c.seniority && (
                          <Badge variant="secondary" className="text-xs">
                            {c.seniority}
                          </Badge>
                        )}
                        <span className="text-xs text-muted-foreground font-mono">
                          {c.email}
                        </span>
                        {c.linkedin_url && (
                          <a
                            href={c.linkedin_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-blue-500 hover:underline"
                          >
                            LinkedIn
                          </a>
                        )}
                      </div>
                    </div>
                    <CopyButton text={c.email} label="Email" />
                  </div>
                ))}
              </div>
            )}

            {contacts.length > 0 && (
              <div className="flex gap-2 pt-2">
                <Button variant="outline" onClick={() => setStep("draft")}>
                  <ArrowLeft className="h-4 w-4 mr-1" /> Back
                </Button>
                <Button onClick={handleAddAllToOutreach} className="gap-2">
                  <Check className="h-4 w-4" /> Save & Continue
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 5: Ready to Send */}
      {step === "send" && (
        <Card>
          <CardHeader>
            <CardTitle>Ready to Send</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2 p-3 rounded-lg bg-muted">
              <div className="flex items-center justify-between">
                <Label className="text-xs text-muted-foreground">SUBJECT</Label>
                <CopyButton text={emailSubject} label="Copy" />
              </div>
              <p className="font-medium">{emailSubject}</p>
            </div>

            <Separator />

            {contacts.map((c) => (
              <div key={c.id} className="space-y-3 p-4 rounded-lg border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      {c.first_name} {c.last_name}
                    </p>
                    <p className="text-sm text-muted-foreground">{c.title}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <CopyButton text={c.email} label="Email addr" />
                    <CopyButton text={emailSubject} label="Subject" />
                    <CopyButton
                      text={buildFullEmail(c.first_name)}
                      label="Full Email"
                    />
                    {linkedinNote && (
                      <CopyButton
                        text={linkedinNote}
                        label="LinkedIn"
                      />
                    )}
                  </div>
                </div>
                {linkedinNote && (
                  <div className="flex items-start gap-2 p-2 rounded bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
                    <Link className="h-3.5 w-3.5 text-blue-500 mt-0.5 shrink-0" />
                    <p className="text-xs text-blue-900 dark:text-blue-100">{linkedinNote}</p>
                  </div>
                )}
                <div className="text-sm bg-muted p-3 rounded whitespace-pre-wrap font-mono">
                  Hey {c.first_name},
                  {"\n\n"}
                  {emailBody}
                  {"\n\n"}
                  {linksBlock}
                  {"\n\n"}
                  {signOff}
                </div>
              </div>
            ))}

            <Button
              onClick={() => navigate(`/applications/${applicationId}`)}
              className="w-full"
            >
              Go to Application Detail
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
