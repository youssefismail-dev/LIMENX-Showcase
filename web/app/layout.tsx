// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/nav";
import { SplineHero } from "@/components/spline-hero";
import { SmoothScrollProvider } from "@/lib/scroll/smooth-scroll-provider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LIMENX — Know before you click.",
  description:
    "An AI cybersecurity platform that analyzes any URL for phishing — instantly, offline, and explainably.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      {/* Dark page background; the fixed Spline hero floats over it and the
          content scrolls above it. */}
      <body className="flex min-h-full flex-col bg-[#06070c] text-neutral-100">
        <SplineHero />
        <Nav />
        <SmoothScrollProvider>{children}</SmoothScrollProvider>
      </body>
    </html>
  );
}
