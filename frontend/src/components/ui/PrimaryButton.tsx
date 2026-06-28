import type { ButtonHTMLAttributes, ReactNode } from "react";
import { RefreshCw } from "lucide-react";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  children: ReactNode;
}

export function PrimaryButton({ loading, children, className = "", disabled, ...props }: PrimaryButtonProps) {
  const isInactive = disabled || loading;
  return (
    <button
      {...props}
      disabled={isInactive}
      className={`magnetic-btn w-full font-semibold py-4 rounded-container flex items-center justify-center gap-2 disabled:opacity-100 ${
        isInactive
          ? "bg-surfaceElevated text-textMuted border border-borderSubtle cursor-not-allowed"
          : "bg-accent text-white"
      } ${className}`}
    >
      {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : children}
    </button>
  );
}

export function SecondaryButton({ children, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`magnetic-btn w-full border border-borderSubtle text-textPrimary font-medium py-3 rounded-container hover:border-accent/40 ${className}`}
    >
      {children}
    </button>
  );
}
