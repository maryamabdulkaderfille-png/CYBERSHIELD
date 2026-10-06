const RULES: { test: (value: string) => boolean; label: string }[] = [
  { test: (v) => v.length >= 8, label: "8+ characters" },
  { test: (v) => /[A-Z]/.test(v), label: "Uppercase letter" },
  { test: (v) => /[a-z]/.test(v), label: "Lowercase letter" },
  { test: (v) => /\d/.test(v), label: "Number" },
  { test: (v) => /[^A-Za-z0-9]/.test(v), label: "Special character" },
];

const STRENGTH_META = [
  { label: "Very weak", classes: "bg-danger" },
  { label: "Weak", classes: "bg-danger" },
  { label: "Fair", classes: "bg-warning" },
  { label: "Good", classes: "bg-warning" },
  { label: "Strong", classes: "bg-safe" },
];

export function PasswordStrengthMeter({ password }: { password: string }) {
  const passed = RULES.map((rule) => rule.test(password));
  const score = passed.filter(Boolean).length;
  const meta = STRENGTH_META[Math.max(score - 1, 0)];

  if (!password) return null;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-1.5">
        {RULES.map((_, index) => (
          <div
            key={index}
            className={`h-1 flex-1 rounded-full transition-colors ${
              index < score ? meta.classes : "bg-white/10"
            }`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {RULES.map((rule, index) => (
          <span
            key={rule.label}
            className={`text-xs ${passed[index] ? "text-safe" : "text-slate-500"}`}
          >
            {passed[index] ? "✓" : "○"} {rule.label}
          </span>
        ))}
      </div>
    </div>
  );
}
