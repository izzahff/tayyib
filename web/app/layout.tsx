import type { Metadata } from "next";
import Link from "next/link";
import "@fontsource-variable/hanken-grotesk";
import "@fontsource/amiri/400.css";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "Tayyib, Shariah stock screening",
  description:
    "An alert-only AAOIFI Shariah screener. It checks stocks on two ratios, ranks the compliant ones by momentum, and keeps an audit trail of every decision.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="masthead">
            <Link href="/" className="brand">
              <span className="brand-arabic" lang="ar" dir="rtl">
                طيّب
              </span>
              <span className="brand-name">Tayyib</span>
            </Link>
            <Nav />
          </header>
          <main>{children}</main>
          <footer className="footer">
            <p>
              For research and education only. Tayyib is not a Shariah board ruling or financial
              advice, and it never places trades. Scores are simulated and past results do not
              predict future ones.
            </p>
            <p className="footer-mark">
              &copy; 2026{" "}
              <a href="https://izzahfff.vercel.app/" target="_blank" rel="noreferrer">
                izzahfff
              </a>
            </p>
          </footer>
        </div>
      </body>
    </html>
  );
}
