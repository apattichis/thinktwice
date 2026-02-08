import type { Metadata } from "next";
import { DM_Sans, JetBrains_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ThinkTwice | Verified AI Answers",
  description:
    "A self-correcting AI pipeline that decomposes constraints, verifies against live sources, and enforces what LLMs can't on their own.",
  keywords: ["AI", "fact-checking", "verification", "reasoning", "instruction-following"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${dmSans.variable} ${jetbrainsMono.variable} font-sans`}>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
