import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Plus, Edit2, Trash2, Sparkles, Loader2 } from "lucide-react";
import api from "@/lib/api";

interface Template {
  id: string;
  slug: string;
  title: string;
  color: string;
  tagline: string;
  system_prompt: string;
  role_prompt_addition: string;
  example_email: string;
  sort_order: number;
}

const EMPTY: Omit<Template, "id"> = {
  slug: "",
  title: "",
  color: "#3b82f6",
  tagline: "",
  system_prompt: "",
  role_prompt_addition: "",
  example_email: "",
  sort_order: 0,
};

export function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [editing, setEditing] = useState<Template | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<any>({ ...EMPTY });
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    const res = await api.get("/api/templates");
    setTemplates(res.data);
  };

  const handleSave = async () => {
    if (editing) {
      await api.put(`/api/templates/${editing.id}`, form);
    } else {
      await api.post("/api/templates", form);
    }
    setEditing(null);
    setCreating(false);
    setForm({ ...EMPTY });
    loadTemplates();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this template?")) return;
    await api.delete(`/api/templates/${id}`);
    loadTemplates();
  };

  const openEdit = (t: Template) => {
    setEditing(t);
    setForm({
      slug: t.slug,
      title: t.title,
      color: t.color,
      tagline: t.tagline,
      system_prompt: t.system_prompt,
      role_prompt_addition: t.role_prompt_addition,
      example_email: t.example_email,
      sort_order: t.sort_order,
    });
    setCreating(true);
  };

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY });
    setCreating(true);
  };

  const generateTemplates = async () => {
    if (!confirm("This will replace ALL your current templates with AI-generated ones based on your profile. Continue?")) return;
    setGenerating(true);
    try {
      await api.post("/api/templates/generate");
      await loadTemplates();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Generation failed. Make sure your profile is filled in first.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Role Templates</h1>
          <p className="text-sm text-muted-foreground mt-1">
            New user? Fill your profile first, then hit Generate.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={generateTemplates}
            disabled={generating}
            className="gap-2"
          >
            {generating ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Generating...</>
            ) : (
              <><Sparkles className="h-4 w-4" /> Generate from Profile</>
            )}
          </Button>
          <Button onClick={openCreate} className="gap-2">
            <Plus className="h-4 w-4" /> New Template
          </Button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {templates.map((t) => (
          <Card key={t.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ background: t.color }}
                  />
                  {t.title}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => openEdit(t)}
                  >
                    <Edit2 className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => handleDelete(t.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {t.tagline && (
                <p className="text-xs text-muted-foreground italic mb-2">
                  {t.tagline}
                </p>
              )}
              <Badge variant="outline" className="text-xs">
                {t.slug}
              </Badge>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={creating} onOpenChange={setCreating}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editing ? "Edit Template" : "New Template"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Title</Label>
                <Input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="AI/ML Engineer"
                />
              </div>
              <div className="space-y-2">
                <Label>Slug</Label>
                <Input
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  placeholder="ai-ml"
                  disabled={!!editing}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Color</Label>
                <Input
                  type="color"
                  value={form.color}
                  onChange={(e) => setForm({ ...form, color: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Tagline</Label>
                <Input
                  value={form.tagline}
                  onChange={(e) =>
                    setForm({ ...form, tagline: e.target.value })
                  }
                  placeholder="Your elevator pitch for this role"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Role Prompt Addition</Label>
              <Textarea
                value={form.role_prompt_addition}
                onChange={(e) =>
                  setForm({ ...form, role_prompt_addition: e.target.value })
                }
                rows={6}
                placeholder="ROLE: AI/ML Engineer&#10;LEAD WITH: ..."
              />
            </div>
            <div className="space-y-2">
              <Label>Example Email</Label>
              <Textarea
                value={form.example_email}
                onChange={(e) =>
                  setForm({ ...form, example_email: e.target.value })
                }
                rows={10}
                placeholder="Subject: ...&#10;&#10;Hey [Name],&#10;..."
              />
            </div>
            <Button onClick={handleSave} className="w-full">
              {editing ? "Update" : "Create"} Template
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
