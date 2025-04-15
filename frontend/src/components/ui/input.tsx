import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * Input component for form controls
 * 
 * This component is a thin wrapper around the native HTML input element
 * with consistent styling and support for all standard input attributes.
 * 
 * @param className - Additional CSS classes to apply
 * @param type - Input type (text, email, password, etc.)
 * @param props - All other HTML input attributes
 */
export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input } 