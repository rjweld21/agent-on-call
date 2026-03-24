import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent On Call",
  description: "Voice-first AI agent platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, background: "#0f172a" }}>
        {children}
      </body>
    </html>
  );
}
