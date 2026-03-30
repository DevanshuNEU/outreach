import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CopyButton({
  text,
  label = "Copy",
  variant = "outline",
  size = "sm",
}: {
  text: string;
  label?: string;
  variant?: "outline" | "ghost" | "secondary";
  size?: "sm" | "default" | "icon";
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <Button variant={variant} size={size} onClick={handleCopy}>
      {copied ? (
        <>
          <Check className="h-3 w-3 mr-1" /> Copied
        </>
      ) : (
        <>
          <Copy className="h-3 w-3 mr-1" /> {label}
        </>
      )}
    </Button>
  );
}
