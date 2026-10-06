import type { InputHTMLAttributes, ReactNode } from "react";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  rightElement?: ReactNode;
}

export function FormField({ label, error, rightElement, id, ...inputProps }: FormFieldProps) {
  const fieldId = id ?? inputProps.name;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={fieldId} className="text-sm font-medium text-slate-300">
        {label}
      </label>
      <div className="relative">
        <input id={fieldId} className="input-field" {...inputProps} />
        {rightElement && <div className="absolute inset-y-0 right-3 flex items-center">{rightElement}</div>}
      </div>
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  );
}
