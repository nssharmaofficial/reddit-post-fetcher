import { cn } from "@/lib/utils"

/**
 * Skeleton component for representing loading states
 * 
 * Use this component to show a placeholder while content is loading
 * to improve perceived performance and reduce layout shifts.
 * 
 * @param className - Additional CSS classes to apply
 * @param props - HTML div element props
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

export { Skeleton } 