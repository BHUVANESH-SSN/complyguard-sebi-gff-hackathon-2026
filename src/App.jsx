import { useState } from "react";
import Nav from "./components/layout/Nav";
import Sidebar from "./components/layout/Sidebar";
import Hero from "./components/views/Hero";
import Landing from "./components/views/Landing";
import UploadCircular from "./components/views/UploadCircular";
import ObligationList from "./components/views/ObligationList";
import GapDashboard from "./components/views/GapDashboard";
import AuditTrail from "./components/views/AuditTrail";
import {
  INITIAL_OBLIGATIONS,
  INITIAL_EVIDENCE,
  INITIAL_AUDIT_LOG,
} from "./data/mockData";

const ALL_VIEWS = ["landing", "upload", "obligations", "dashboard", "audit"];

export default function App() {
  const [view, setView] = useState("landing");
  const [unlocked, setUnlocked] = useState(["landing", "upload"]);
  const [obligations, setObligations] = useState(INITIAL_OBLIGATIONS);
  const [evidence, setEvidence] = useState(INITIAL_EVIDENCE);
  const [auditLog, setAuditLog] = useState(INITIAL_AUDIT_LOG);

  function handleUploadComplete() {
    setUnlocked(ALL_VIEWS); // full nav available once the pipeline has "run"
    setView("obligations");
  }

  function handleStart() {
    setUnlocked((prev) => (prev.includes("upload") ? prev : [...prev, "upload"]));
    setView("upload");
  }

  function handleAttachEvidence(obligationId, description) {
    const ob = obligations.find((o) => o.id === obligationId);

    setEvidence((prev) => [
      ...prev,
      {
        id: prev.length + 1,
        obligationId,
        description,
        submittedAt: new Date().toISOString(),
      },
    ]);
    setObligations((prev) =>
      prev.map((o) => (o.id === obligationId ? { ...o, status: "met" } : o))
    );
    setAuditLog((prev) => [
      ...prev,
      {
        id: prev.length + 1,
        action: "Evidence added",
        detail: `Evidence attached to obligation #${obligationId} (${ob?.obligationText.slice(0, 50)}...).`,
        timestamp: new Date().toISOString(),
      },
      {
        id: prev.length + 2,
        action: "Status updated",
        detail: `Obligation #${obligationId} moved to "met".`,
        timestamp: new Date().toISOString(),
      },
    ]);
  }

  return (
    <div className="min-h-screen bg-white">
      <Nav view={view} setView={setView} unlocked={unlocked} />
      {view === "landing" && <Hero onStart={handleStart} />}

      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10 lg:flex-row">
        {view === "landing" && <Landing />}
        {view === "upload" && <UploadCircular onComplete={handleUploadComplete} />}
        {view === "obligations" && (
          <ObligationList
            obligations={obligations}
            evidence={evidence}
            onAttachEvidence={handleAttachEvidence}
          />
        )}
        {view === "dashboard" && (
          <GapDashboard
            obligations={obligations}
            onSelectObligation={() => setView("obligations")}
          />
        )}
        {view === "audit" && <AuditTrail log={auditLog} />}

        <Sidebar
          obligations={obligations}
          evidence={evidence}
          auditLog={auditLog}
          onOpenDashboard={() => setView("dashboard")}
        />
      </div>

      <footer className="border-t border-neutral-100 py-8 text-center text-xs text-neutral-300">
        ComplyGuard prototype — mock data, no backend yet. Built from docs/plan.md.
      </footer>
    </div>
  );
}
