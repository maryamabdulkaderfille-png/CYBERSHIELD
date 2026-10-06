import { AlertTriangle } from "lucide-react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  isDangerous?: boolean;
  isSubmitting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Generic confirmation modal for destructive-ish admin actions (suspend,
 * remove, ...) — matches the existing glass-card design system. No
 * confirmation pattern existed anywhere in the app before this; kept
 * intentionally minimal/reusable rather than one-off per action. */
export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  isDangerous = true,
  isSubmitting = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true">
      <div className="glass-card w-full max-w-sm p-6">
        <div className="flex items-start gap-3">
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
              isDangerous ? "bg-danger/10 text-danger" : "bg-warning/10 text-warning"
            }`}
          >
            <AlertTriangle size={18} />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">{title}</h2>
            <p className="mt-1.5 text-sm text-slate-400">{message}</p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button onClick={onCancel} disabled={isSubmitting} className="btn-secondary px-4 py-2">
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isSubmitting}
            className={`px-4 py-2 text-sm font-medium rounded-xl transition-colors ${
              isDangerous
                ? "bg-danger/90 text-white hover:bg-danger disabled:opacity-50"
                : "btn-primary disabled:opacity-50"
            }`}
          >
            {isSubmitting ? "Working…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
