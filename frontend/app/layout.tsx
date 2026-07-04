import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Toaster } from "sonner";
import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/top-bar";
import { LiveStoreProvider } from "@/components/live-store-provider";

export const metadata: Metadata = {
  title: "Office Energy Monitor",
  description: "Real-time office energy monitoring across 3 rooms and 15 devices.",
};

export const viewport: Viewport = {
  themeColor: "#0b1020",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-ambient min-h-screen">
        <LiveStoreProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex flex-1 flex-col">
              <TopBar />
              <main className="flex-1 p-4 md:p-6 lg:p-8">{children}</main>
            </div>
          </div>
          <Toaster theme="dark" position="top-right" richColors closeButton />
        </LiveStoreProvider>
      </body>
    </html>
  );
}