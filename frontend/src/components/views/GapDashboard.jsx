import StatusBadge from "../shared/StatusBadge";

export default function GapDashboard({ obligations, onSelectObligation }) {
  const met = obligations.filter((o) => o.status === "met");
  const overdue = obligations.filter((o) => o.status === "overdue");
  const pending = obligations.filter((o) => o.status === "pending");
  const gaps = [...overdue, ...pending];

  const cards = [
    { label: "Met", value: met.length, tone: "bg-emerald-50 text-emerald-700" },
    { label: "Pending", value: pending.length, tone: "bg-amber-50 text-amber-700" },
    { label: "Overdue", value: overdue.length, tone: "bg-red-50 text-red-700" },
  ];

  return (
    <div className="flex-1">
      <h2 className="text-2xl font-bold tracking-tight text-neutral-900">
        Gap dashboard
      </h2>
      <p className="mt-2 text-sm text-neutral-500">
        A gap is any obligation with no evidence on file, or a deadline that
        has passed.
      </p>

      <div className="mt-6 grid grid-cols-3 gap-4">
        {cards.map((c) => (
          <div key={c.label} className={`rounded-2xl p-5 ${c.tone}`}>
            <p className="font-mono text-3xl font-bold">{c.value}</p>
            <p className="mt-1 text-sm font-medium">{c.label}</p>
          </div>
        ))}
      </div>

      <div className="mt-8">
        <p className="font-mono text-xs font-medium tracking-wide text-neutral-400">
          {gaps.length} OBLIGATION{gaps.length === 1 ? "" : "S"} NEED ATTENTION
        </p>
        <div className="mt-3 space-y-3">
          {gaps.length === 0 && (
            <p className="rounded-2xl border border-neutral-200 p-5 text-sm text-neutral-400">
              No gaps. Everything is met.
            </p>
          )}
          {gaps.map((ob) => (
            <button
              key={ob.id}
              onClick={() => onSelectObligation(ob.id)}
              className="flex w-full items-start justify-between gap-4 rounded-2xl border border-neutral-200 p-5 text-left hover:border-violet-200 hover:bg-violet-50/30"
            >
              <div>
                <p className="text-sm font-medium text-neutral-900">
                  {ob.obligationText}
                </p>
                <p className="mt-1.5 font-mono text-xs text-neutral-400">
                  Deadline: {ob.deadline ?? "Not specified"}
                </p>
              </div>
              <StatusBadge status={ob.status} />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
