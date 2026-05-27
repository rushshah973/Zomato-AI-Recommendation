import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Zomato AI - Gourmet Advisor',
  description: 'AI-Native Restaurant Discovery Dashboard powered by Gemini & Zomato',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
