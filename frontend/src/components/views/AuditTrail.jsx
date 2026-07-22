const AUTOMATED_ACTIONS = ["Circular ingested", "Obligations extracted", "Gap check run"];

function dayOf(ts) {
  return new Date(ts).getDate().toString().padStart(2, "0");
}
function monthOf(ts) {
  return new Date(ts).toLocaleString("en-US", { month: "short" }).toUpperCase();
}

export default function AuditTrail({ log }) {
  const sorted = [...log].sort(
    (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
  );

  return (
    <div className="flex-1">
      <h2 className="text-2xl font-bold tracking-tight text-neutral-900">
        Audit trail
      </h2>
      <p className="mt-2 text-sm text-neutral-500">
        An immutable log of every action taken on this circular — the record
        that makes compliance auditable, not just tracked.
      </p>

      <div className="relative mt-8">
        <div className="absolute bottom-0 left-[35px] top-0 w-px bg-violet-100" />
        <div className="space-y-5">
          {sorted.map((entry) => {
            const automated = AUTOMATED_ACTIONS.includes(entry.action);
            return (
              <div key={entry.id} className="relative flex items-start gap-5">
                <div className="z-10 flex h-[70px] w-[70px] flex-shrink-0 flex-col items-center justify-center rounded-xl bg-gradient-to-br from-violet-700 to-indigo-800 text-white shadow-sm">
                  <span className="text-lg font-bold leading-none">
                    {dayOf(entry.timestamp)}
                  </span>
                  <span className="mt-1 font-mono text-[10px] tracking-widest text-violet-200">
                    {monthOf(entry.timestamp)}
                  </span>
                </div>

                <div className="flex-1 rounded-2xl border border-neutral-200 p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-neutral-900">{entry.action}</p>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        automated
                          ? "bg-violet-50 text-violet-700"
                          : "bg-amber-50 text-amber-700"
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          automated ? "bg-violet-500" : "bg-amber-500"
                        }`}
                      />
                      {automated ? "Automated" : "Manual"}
                    </span>
                  </div>
                  <p className="mt-1.5 text-sm text-neutral-500">{entry.detail}</p>
                  <p className="mt-3 border-t border-neutral-100 pt-3 font-mono text-xs text-neutral-400">
                    {new Date(entry.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
