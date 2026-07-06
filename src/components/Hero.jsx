import { CIRCULAR } from "../data/mockData";
import sebiLogo from "../assets/sebi-logo.png";

export default function Hero({ onStart }) {
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-indigo-950 via-violet-900 to-purple-800">
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.4) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      <div className="relative mx-auto grid max-w-6xl grid-cols-1 gap-10 px-6 py-14 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white p-1 ring-1 ring-white/20">
              <img src={sebiLogo} alt="SEBI" className="h-full w-full object-contain" />
            </div>
            <span className="font-mono text-xs tracking-widest text-violet-200">
              {CIRCULAR.issuedBy} AGENTIC COMPLIANCE
            </span>
          </div>

          <h1 className="mt-5 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            From regulatory text to operational action.
          </h1>
          <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-violet-100/80">
            Upload a SEBI circular. ComplyGuard reads it, extracts every
            obligation it imposes, and flags what's unmet — automatically and
            auditably.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 font-mono text-xs text-violet-200">
            <span className="flex items-center gap-1.5">
              📅 {CIRCULAR.pages} pages parsed
            </span>
            <span className="flex items-center gap-1.5">
              🏷 Intermediary: {CIRCULAR.intermediary}
            </span>
          </div>

          <div className="mt-8 flex items-center gap-3">
            <button
              onClick={onStart}
              className="rounded-full bg-emerald-300 px-6 py-3 text-sm font-semibold text-emerald-950 transition-colors hover:bg-emerald-400"
            >
              Try the demo →
            </button>
          </div>
        </div>

        <div className="relative hidden aspect-[4/3] items-center justify-center rounded-2xl bg-gradient-to-br from-violet-800/60 to-indigo-950/60 ring-1 ring-white/10 lg:flex">
          <div className="absolute -top-10 -right-10 h-40 w-40 rounded-full bg-fuchsia-500/20 blur-3xl" />
          <div className="absolute -bottom-10 -left-10 h-40 w-40 rounded-full bg-indigo-400/20 blur-3xl" />
          <img
            src={sebiLogo}
            alt="SEBI"
            className="relative w-2/3 max-w-[220px] opacity-80"
          />
        </div>
      </div>
    </div>
  );
}
