import { createFileRoute } from "@tanstack/react-router";
import { AegisDashboard } from "@/components/aegis/AegisDashboard";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Project Aegis — Ransomware Interception & Stasis" },
      {
        name: "description",
        content:
          "Aegis intercepts ransomware in real time using Shannon entropy — no ML, no signatures. Watch encryption get detected, frozen and rolled back live.",
      },
      { property: "og:title", content: "Project Aegis — Ransomware Interception & Stasis" },
      {
        property: "og:description",
        content:
          "Deterministic ransomware defence for SMEs: entropy-based detection, process stasis, one-click restore.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AegisDashboard,
});
