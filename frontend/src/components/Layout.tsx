import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  PlusCircle,
  List,
  FileText,
  User,
  LogOut,
  Zap,
  TrendingUp,
} from "lucide-react";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/fit", label: "Fit Check", icon: Zap },
  { path: "/outreach/new", label: "New Outreach", icon: PlusCircle },
  { path: "/tracker", label: "Tracker", icon: List },
  { path: "/analytics", label: "Analytics", icon: TrendingUp },
  { path: "/templates", label: "Templates", icon: FileText },
  { path: "/profile", label: "Profile", icon: User },
];

export function Layout({
  children,
  onLogout,
  username,
}: {
  children: React.ReactNode;
  onLogout: () => void;
  username: string;
}) {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="font-semibold text-lg">
              Outreach
            </Link>
            <nav className="hidden md:flex items-center gap-1">
              {NAV_ITEMS.map((item) => (
                <Button
                  key={item.path}
                  variant={
                    location.pathname === item.path ? "secondary" : "ghost"
                  }
                  size="sm"
                  onClick={() => navigate(item.path)}
                  className="gap-2"
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">{username}</span>
            <Button variant="ghost" size="icon" onClick={onLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
