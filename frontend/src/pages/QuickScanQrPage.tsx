import { motion } from "framer-motion";
import { Camera, Clipboard as ClipboardIcon, QrCode, Upload, X } from "lucide-react";
import { useEffect, useRef, useState, type DragEvent } from "react";
import { Link } from "react-router-dom";

import { QrScanResultCard } from "@/components/qrScanner/QrScanResultCard";
import { extractErrorMessage } from "@/lib/errors";
import * as guestScanService from "@/services/guestScanService";
import type { QRScanReport } from "@/types/qrScan";

const ACCEPTED_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);
const MAX_BYTES = 5 * 1024 * 1024;

export function QuickScanQrPage() {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<QRScanReport | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFile = async (file: File) => {
    setError(null);

    if (!ACCEPTED_TYPES.has(file.type)) {
      setError("Unsupported file type. Please use a PNG, JPEG, or WEBP image.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("Image is too large (max 5 MB).");
      return;
    }

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(file));
    setReport(null);
    setIsScanning(true);

    try {
      const result = await guestScanService.guestScanQrImage(file);
      setReport(result);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not analyze this QR code. Please try another image."));
    } finally {
      setIsScanning(false);
    }
  };

  // Paste-an-image-from-clipboard support.
  useEffect(() => {
    const handlePaste = (event: ClipboardEvent) => {
      const items = event.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) {
            handleFile(file);
            return;
          }
        }
      }
    };
    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [previewUrl]);

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDraggingOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleClear = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setReport(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (cameraInputRef.current) cameraInputRef.current.value = "";
  };

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <Link to="/quick-scan" className="text-xs font-medium text-slate-500 hover:text-slate-300">
        ← Back to Quick Scan
      </Link>

      <div className="mt-4">
        <h1 className="text-2xl font-bold text-slate-50">Scan QR</h1>
        <p className="mt-1 text-sm text-slate-400">
          Upload, drag & drop, paste, or capture a QR code to check what it really points to. No account required —
          guest scan results are not saved to your account.
        </p>
      </div>

      <div className="glass-card mt-6 p-6">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDraggingOver(true);
          }}
          onDragLeave={() => setIsDraggingOver(false)}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed px-6 py-10 text-center transition-colors ${
            isDraggingOver ? "border-brand-cyan/60 bg-brand-cyan/5" : "border-white/15 bg-white/[0.02]"
          }`}
        >
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="QR code preview"
              className="h-40 w-40 rounded-xl border border-white/10 object-contain"
            />
          ) : (
            <QrCode size={32} className="text-slate-500" />
          )}

          <p className="text-sm text-slate-300">
            {previewUrl ? "Drop a new image to scan again" : "Drag & drop a QR image here, or paste one (Ctrl/Cmd+V)"}
          </p>
          <p className="text-xs text-slate-500">PNG, JPEG, or WEBP · Max 5 MB</p>

          <div className="flex flex-wrap justify-center gap-3">
            <button type="button" onClick={() => fileInputRef.current?.click()} className="btn-primary px-5">
              <Upload size={16} />
              Upload Image
            </button>
            <button type="button" onClick={() => cameraInputRef.current?.click()} className="btn-secondary px-5">
              <Camera size={16} />
              Use Camera
            </button>
            {previewUrl && (
              <button type="button" onClick={handleClear} className="btn-secondary px-5">
                <X size={16} />
                Clear
              </button>
            )}
          </div>

          <p className="flex items-center gap-1.5 text-xs text-slate-600">
            <ClipboardIcon size={12} />
            Tip: copy a QR image and press Ctrl/Cmd+V anywhere on this page
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </div>

        {error && <p className="mt-4 text-sm text-danger">{error}</p>}
      </div>

      {isScanning && (
        <div className="glass-card mt-6 flex flex-col items-center gap-4 p-10">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
            className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-blue to-brand-cyan"
          >
            <QrCode size={26} className="text-navy-950" />
          </motion.div>
          <p className="text-sm text-slate-400">Decoding and analyzing QR code…</p>
        </div>
      )}

      {report && !isScanning && (
        <div className="mt-6">
          <QrScanResultCard report={report} />
          <p className="mt-6 text-center text-xs text-slate-500">
            Want to keep your scan history?{" "}
            <Link to="/register" className="font-medium text-brand-cyan hover:underline">
              Create a free account
            </Link>
            .
          </p>
        </div>
      )}
    </div>
  );
}
