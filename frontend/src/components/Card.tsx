import { PropsWithChildren } from "react";
import { cn } from "../lib/cn";

export const Card = ({ children, className }: PropsWithChildren<{ className?: string }>) => (
  <div className={cn("rounded-lg border bg-white shadow-sm", className)}>{children}</div>
);

export const CardHeader = ({ children }: PropsWithChildren) => (
  <div className="border-b px-4 py-3 text-sm font-medium text-slate-500">{children}</div>
);

export const CardTitle = ({ children }: PropsWithChildren) => (
  <div className="text-base font-semibold text-slate-900">{children}</div>
);

export const CardContent = ({ children }: PropsWithChildren) => (
  <div className="space-y-2 px-4 py-6 text-slate-900">{children}</div>
);
