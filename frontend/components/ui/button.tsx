import * as React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline";
  size?: "default" | "sm";
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "default", size = "default", ...props }, ref) => {
    const variantClass =
      variant === "outline"
        ? "border border-slate-300 bg-white text-slate-900 hover:bg-slate-50"
        : "bg-slate-900 text-white hover:bg-slate-800";
    const sizeClass = size === "sm" ? "px-3 py-1.5 text-sm" : "px-4 py-2 text-sm";

    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center rounded-md font-medium disabled:cursor-not-allowed disabled:opacity-50 ${variantClass} ${sizeClass} ${className}`}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
