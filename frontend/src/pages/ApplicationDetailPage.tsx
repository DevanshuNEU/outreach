import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CopyButton } from "@/components/CopyButton";
import { FollowUpTimeline } from "@/components/FollowUpTimeline";
import { Check, X, Send, Link } from "lucide-react";
import api from "@/lib/api";

interface Outreach {
  id: string;
  contact_id: string;
  personalized_greeting: string;
  sent_at: string | null;
  followup_1_sent_at: string | null;
  followup_2_sent_at: string | null;
  followup_3_sent_at: string | null;
  replied: boolean;
  reply_date: string | null;
  contact: {
    id: string;
    first_name: string;
    last_name: string;
    title: string;
    email: string;
    seniority: string;
    linkedin_url: string | null;
  } | null;
}

export function ApplicationDetailPage() {
  const { id } = useParams();

  const [app, setApp] = useState<any>(null);
  const [company, setCompany] = useState<any>(null);
  const [outreach, setOutreach] = useState<Outreach[]>([]);
  const [signOff, setSignOff] = useState("");
  const [linksBlock, setLinksBlock] = useState("");

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    const [appRes, profileRes] = await Promise.all([
      api.get(`/api/applications/${id}`),
      api.get("/api/profile"),
    ]);
    setApp(appRes.data);
    setSignOff(profileRes.data.sign_off_block || "");
    setLinksBlock(profileRes.data.links_block || "");

    if (appRes.data.company_id) {
      const companies = await api.get("/api/companies");
      const c = companies.data.find(
        (co: any) => co.id === appRes.data.company_id
      );
      setCompany(c);
    }

    const outreachRes = await api.get(
      `/api/outreach?application_id=${id}`
    );
    setOutreach(outreachRes.data);
  };

  const toggleSent = async (o: Outreach) => {
    const now = new Date().toISOString();
    await api.put(`/api/outreach/${o.id}`, {
      sent_at: o.sent_at ? null : now,
    });
    loadData();
  };

  const toggleReplied = async (o: Outreach) => {
    await api.put(`/api/outreach/${o.id}`, { replied: !o.replied });
    loadData();
  };

  const markFollowUpSent = async (outreachId: string, field: string) => {
    await api.put(`/api/outreach/${outreachId}`, {
      [field]: new Date().toISOString(),
    });
    loadData();
  };

  const buildFullEmail = (firstName: string) => {
    return `Hey ${firstName},\n\n${app?.email_body || ""}\n\n${linksBlock}\n\n${signOff}`;
  };

  if (!app) return <p>Loading...</p>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{company?.name || "Company"}</h1>
          <p className="text-muted-foreground">
            {app.job_title} {company?.location && `- ${company.location}`}
          </p>
        </div>
        <Badge variant="outline">{app.status.replace(/_/g, " ")}</Badge>
      </div>

      <Tabs defaultValue="outreach">
        <TabsList>
          <TabsTrigger value="outreach">Outreach</TabsTrigger>
          <TabsTrigger value="email">Email Draft</TabsTrigger>
          <TabsTrigger value="jd">Job Description</TabsTrigger>
        </TabsList>

        <TabsContent value="outreach" className="space-y-4">
          {outreach.length === 0 ? (
            <Card>
              <CardContent className="py-6 text-center text-muted-foreground">
                No outreach yet for this application.
              </CardContent>
            </Card>
          ) : (
            outreach.map((o) => (
              <Card key={o.id}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">
                        {o.contact?.first_name} {o.contact?.last_name}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {o.contact?.title}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {o.contact?.email}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <CopyButton
                        text={o.contact?.email || ""}
                        label="Email"
                      />
                      <CopyButton text={app.email_subject || ""} label="Subject" />
                      <CopyButton
                        text={buildFullEmail(o.contact?.first_name || "")}
                        label="Full Email"
                      />
                      {o.contact?.linkedin_url && (
                        <a
                          href={o.contact.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <Button variant="outline" size="sm" className="gap-1">
                            <Link className="h-3 w-3" />
                            LinkedIn
                          </Button>
                        </a>
                      )}
                      {app.linkedin_note && (
                        <CopyButton text={app.linkedin_note} label="LI Note" />
                      )}
                      <Separator orientation="vertical" className="h-6" />
                      <Button
                        variant={o.sent_at ? "default" : "outline"}
                        size="sm"
                        onClick={() => toggleSent(o)}
                        className="gap-1"
                      >
                        <Send className="h-3 w-3" />
                        {o.sent_at ? "Sent" : "Mark Sent"}
                      </Button>
                      <Button
                        variant={o.replied ? "default" : "outline"}
                        size="sm"
                        onClick={() => toggleReplied(o)}
                        className="gap-1"
                      >
                        {o.replied ? (
                          <Check className="h-3 w-3" />
                        ) : (
                          <X className="h-3 w-3" />
                        )}
                        {o.replied ? "Replied" : "No Reply"}
                      </Button>
                    </div>
                  </div>
                  {app.linkedin_note && (
                    <div className="flex items-start gap-2 p-2 rounded bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 mt-2">
                      <Link className="h-3.5 w-3.5 text-blue-500 mt-0.5 shrink-0" />
                      <p className="text-xs text-blue-900 dark:text-blue-100">
                        {app.linkedin_note}
                      </p>
                    </div>
                  )}
                  {o.sent_at && (
                    <div className="mt-3 pt-3 border-t">
                      <FollowUpTimeline
                        outreach={o}
                        onMarkSent={markFollowUpSent}
                        followupBodies={{
                          fu1: app.followup_1_body,
                          fu2: app.followup_2_body,
                          fu3: app.followup_3_body,
                        }}
                      />
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="email" className="space-y-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Initial Email</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-xs text-muted-foreground">Subject</Label>
                <p className="font-medium">{app.email_subject || "No subject"}</p>
              </div>
              <Separator />
              <pre className="whitespace-pre-wrap text-sm font-mono">
                {app.email_body || "No draft yet"}
              </pre>
              <Separator />
              <pre className="whitespace-pre-wrap text-sm text-muted-foreground">
                {linksBlock}
              </pre>
              <pre className="whitespace-pre-wrap text-sm text-muted-foreground">
                {signOff}
              </pre>
            </CardContent>
          </Card>

          {/* Follow-up drafts */}
          {[
            { label: "FU1 — Day 3", body: app.followup_1_body },
            { label: "FU2 — Day 10", body: app.followup_2_body },
            { label: "FU3 — Day 17", body: app.followup_3_body },
          ].map(({ label, body }) => body ? (
            <Card key={label}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm text-muted-foreground">{label}</CardTitle>
                  <CopyButton text={body} label="Copy" />
                </div>
              </CardHeader>
              <CardContent>
                <pre className="whitespace-pre-wrap text-sm font-mono">{body}</pre>
                <Separator className="my-2" />
                <pre className="whitespace-pre-wrap text-xs text-muted-foreground">{linksBlock}</pre>
                <pre className="whitespace-pre-wrap text-xs text-muted-foreground">{signOff}</pre>
              </CardContent>
            </Card>
          ) : null)}
        </TabsContent>

        <TabsContent value="jd">
          <Card>
            <CardContent className="py-4">
              <pre className="whitespace-pre-wrap text-sm">
                {app.job_description || "No JD provided"}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={className}>{children}</p>;
}
