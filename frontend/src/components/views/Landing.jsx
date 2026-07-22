import { HOW_IT_WORKS } from "../../data/mockData";

export default function Landing() {
  return (
    <div className="flex-1">
      <div className="rounded-2xl border border-neutral-200 p-6">
        <div className="rounded-xl bg-gradient-to-r from-violet-700 to-indigo-800 px-6 py-5 text-white">
          <p className="text-lg font-semibold">SEBI Agentic Compliance</p>
          <p className="mt-1 text-sm text-violet-100/90">
            Text goes in → actionable, auditable compliance comes out.
          </p>
        </div>

        <p className="mt-6 text-sm leading-relaxed text-neutral-500">
          A working prototype where a compliance officer uploads a SEBI
          circular, and the system reads it, extracts the specific
          obligations it imposes on stockbrokers, turns each into a trackable
          checklist item, lets the officer attach evidence of compliance, and
          shows a live dashboard flagging what's unmet or overdue.
        </p>

        <p className="mt-6 font-mono text-xs font-medium tracking-wide text-neutral-400">
          HOW IT WORKS
        </p>
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {HOW_IT_WORKS.map((s) => (
            <div key={s.step} className="rounded-xl border border-neutral-200 p-4">
              <p className="font-mono text-[11px] font-medium text-violet-700">
                {s.step}
              </p>
              <p className="mt-1.5 font-medium text-neutral-900">{s.title}</p>
              <p className="mt-1 text-sm leading-relaxed text-neutral-500">
                {s.text}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-xl bg-neutral-50 p-5">
          <p className="text-sm font-medium text-neutral-900">
            Scope of this prototype
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-neutral-500">
            One circular — the SEBI Master Circular for Stock Brokers. One
            intermediary category. Seven extracted obligations. A working
            end-to-end slice: upload → extract → checklist → evidence → gap
            dashboard → audit trail.
          </p>
        </div>
      </div>
    </div>
  );
}
