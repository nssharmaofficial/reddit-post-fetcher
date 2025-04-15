import type { Metadata } from 'next';
import { Nunito } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/toaster';
import { ToastProvider } from '@/components/ui/use-toast';

// Load Nunito font
const nunito = Nunito({ 
  subsets: ['latin'],
  weight: ['300', '400', '600', '700'],
  variable: '--font-sans'
});

export const metadata: Metadata = {
  title: 'Reddit Post Fetcher',
  description: 'View the latest posts from any subreddit using the Reddit API',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className={`${nunito.className} ${nunito.variable} min-h-screen bg-background font-sans antialiased`}>
        <ToastProvider>
          {children}
          <Toaster />
        </ToastProvider>
      </body>
    </html>
  );
} 