import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Combines multiple class names or class name functions together
 * and resolves any conflicts using tailwind-merge
 * 
 * @param inputs - Class name inputs (strings, objects, arrays, etc.)
 * @returns Merged class string with resolved conflicts
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

/**
 * Format a timestamp to a human-readable string
 */
export function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString();
}

/**
 * Truncate text to a specific length with ellipsis
 */
export function truncateText(text: string, maxLength: number = 200): string {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

/**
 * Get a color for a sentiment
 */
export function getSentimentColor(sentiment: string): string {
  const sentimentColors: Record<string, string> = {
    positive: "green",
    negative: "red",
    neutral: "gray",
    mixed: "yellow",
  };
  
  return sentimentColors[sentiment.toLowerCase()] || "gray";
} 