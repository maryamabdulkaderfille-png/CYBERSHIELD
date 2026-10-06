import { Eye, EyeOff, Lock, Unlock, Wifi } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Badge } from "@/components/common/Badge";
import type { QRContentType } from "@/types/qrScan";

interface QrContentDisplayProps {
  contentType: QRContentType;
  rawContent: string;
  parsedFields: Record<string, unknown>;
}

/** Renders decoded QR content as plain text only — never as HTML, never
 * executed. React already escapes all string interpolation by default; this
 * component additionally never uses dangerouslySetInnerHTML anywhere. */
export function QrContentDisplay({ contentType, rawContent, parsedFields }: QrContentDisplayProps) {
  const [showRaw, setShowRaw] = useState(false);

  const field = (key: string): string => {
    const value = parsedFields[key];
    return value === null || value === undefined ? "—" : String(value);
  };

  return (
    <div className="flex flex-col gap-3">
      {contentType === "url" && (
        <Row label="URL">
          <span className="break-all font-mono text-sm">{field("url")}</span>
        </Row>
      )}

      {contentType === "email" && (
        <>
          <Row label="Recipient">{field("address")}</Row>
          {parsedFields.subject != null && <Row label="Subject">{field("subject")}</Row>}
          {parsedFields.body != null && <Row label="Body">{field("body")}</Row>}
        </>
      )}

      {contentType === "phone" && <Row label="Number">{field("number")}</Row>}

      {contentType === "sms" && (
        <>
          <Row label="Number">{field("number")}</Row>
          {parsedFields.message != null && <Row label="Message">{field("message")}</Row>}
        </>
      )}

      {contentType === "wifi" && (
        <>
          <Row label="Network name (SSID)">
            <span className="inline-flex items-center gap-2">
              <Wifi size={14} />
              {field("ssid")}
            </span>
          </Row>
          <Row label="Security">{field("authentication")}</Row>
          <Row label="Hidden network">{parsedFields.hidden ? "Yes" : "No"}</Row>
          <Row label="Password">
            <span className="inline-flex items-center gap-1.5 text-slate-500">
              {parsedFields.has_password ? <Lock size={13} /> : <Unlock size={13} />}
              {parsedFields.has_password ? "Protected (not shown)" : "None"}
            </span>
          </Row>
        </>
      )}

      {contentType === "crypto" && (
        <>
          <Row label="Network">{field("network")}</Row>
          <Row label="Address">
            <span className="break-all font-mono text-sm">{field("address")}</span>
          </Row>
          <Row label="Format">
            <Badge variant={parsedFields.is_valid_format ? "safe" : "danger"}>
              {parsedFields.is_valid_format ? "Valid" : "Invalid"}
            </Badge>
          </Row>
        </>
      )}

      {contentType === "plain_text" && <Row label="Text">{field("text")}</Row>}

      {contentType === "unknown" && (
        <p className="text-sm text-slate-500">This QR code's content could not be classified.</p>
      )}

      <div className="border-t border-white/10 pt-3">
        <button
          onClick={() => setShowRaw((prev) => !prev)}
          className="flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-300"
        >
          {showRaw ? <EyeOff size={13} /> : <Eye size={13} />}
          {showRaw ? "Hide" : "Show"} raw decoded content
        </button>
        {showRaw && (
          <p className="mt-2 break-all rounded-lg bg-white/[0.03] p-3 font-mono text-xs text-slate-400">
            {rawContent}
          </p>
        )}
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm text-slate-200">{children}</p>
    </div>
  );
}
