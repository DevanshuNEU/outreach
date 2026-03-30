import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2, Save } from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

interface Project {
  name: string;
  description: string;
  metrics: string;
  url: string;
}

export function ProfilePage() {
  const [fullName, setFullName] = useState("");
  const [background, setBackground] = useState("");
  const [signOffBlock, setSignOffBlock] = useState("");
  const [linksBlock, setLinksBlock] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get("/api/profile").then((r) => {
      const p = r.data;
      setFullName(p.full_name || "");
      setBackground(p.background || "");
      setSignOffBlock(p.sign_off_block || "");
      setLinksBlock(p.links_block || "");
      setProjects(p.projects || []);
    });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/api/profile", {
        full_name: fullName,
        background,
        sign_off_block: signOffBlock,
        links_block: linksBlock,
        projects,
      });
      toast.success("Profile saved");
    } catch {
      toast.error("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const addProject = () => {
    setProjects([...projects, { name: "", description: "", metrics: "", url: "" }]);
  };

  const updateProject = (i: number, field: keyof Project, value: string) => {
    const updated = [...projects];
    updated[i] = { ...updated[i], [field]: value };
    setProjects(updated);
  };

  const removeProject = (i: number) => {
    setProjects(projects.filter((_, idx) => idx !== i));
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Profile</h1>
        <Button onClick={handleSave} disabled={saving} className="gap-2">
          <Save className="h-4 w-4" />
          {saving ? "Saving..." : "Save"}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Basic Info</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Full Name</Label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Background</Label>
            <Textarea
              value={background}
              onChange={(e) => setBackground(e.target.value)}
              rows={4}
              placeholder="Your experience summary for AI to reference when drafting emails..."
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Email Sign-off & Links</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Links Block</Label>
            <Textarea
              value={linksBlock}
              onChange={(e) => setLinksBlock(e.target.value)}
              rows={3}
              placeholder={"Live: https://...\nGitHub: https://...\nPortfolio: https://..."}
            />
          </div>
          <div className="space-y-2">
            <Label>Sign-off Block</Label>
            <Textarea
              value={signOffBlock}
              onChange={(e) => setSignOffBlock(e.target.value)}
              rows={5}
              placeholder={"Best,\nYour Name\n..."}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center justify-between">
            Projects
            <Button variant="outline" size="sm" onClick={addProject} className="gap-1">
              <Plus className="h-3 w-3" /> Add Project
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {projects.map((p, i) => (
            <div key={i} className="space-y-3 p-4 rounded-lg border">
              <div className="flex items-center justify-between">
                <Label className="text-xs text-muted-foreground">Project {i + 1}</Label>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => removeProject(i)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Input
                  placeholder="Project name"
                  value={p.name}
                  onChange={(e) => updateProject(i, "name", e.target.value)}
                />
                <Input
                  placeholder="Key metrics"
                  value={p.metrics}
                  onChange={(e) => updateProject(i, "metrics", e.target.value)}
                />
              </div>
              <Textarea
                placeholder="Description"
                value={p.description}
                onChange={(e) => updateProject(i, "description", e.target.value)}
                rows={2}
              />
              <Input
                placeholder="URL (optional)"
                value={p.url}
                onChange={(e) => updateProject(i, "url", e.target.value)}
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
