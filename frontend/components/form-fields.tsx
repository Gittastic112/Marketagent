import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

type FieldProps = {
  id: string;
  label: string;
  className?: string;
};

export function TextField({
  id,
  label,
  className = "field",
  ...inputProps
}: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className={className}>
      <label htmlFor={id}>{label}</label>
      <input id={id} {...inputProps} />
    </div>
  );
}

export function TextAreaField({
  id,
  label,
  className = "field",
  ...textareaProps
}: FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <div className={className}>
      <label htmlFor={id}>{label}</label>
      <textarea id={id} {...textareaProps} />
    </div>
  );
}

export function SelectField({
  id,
  label,
  className = "field",
  children,
  ...selectProps
}: FieldProps & SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode }) {
  return (
    <div className={className}>
      <label htmlFor={id}>{label}</label>
      <select id={id} {...selectProps}>
        {children}
      </select>
    </div>
  );
}

export function CheckboxField({
  id,
  label,
  checkboxLabel,
  name,
  className = "field",
  defaultChecked
}: {
  id: string;
  label: string;
  checkboxLabel?: string;
  name: string;
  className?: string;
  defaultChecked?: boolean;
}) {
  return (
    <div className={className}>
      <label htmlFor={id}>{label}</label>
      <div className="checkbox-row">
        <input defaultChecked={defaultChecked} id={id} name={name} type="checkbox" />
        <span>{checkboxLabel ?? label}</span>
      </div>
    </div>
  );
}
