const STYLES = {
  met: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  overdue: "bg-red-50 text-red-700",
};

const DOT = {
  met: "bg-emerald-500",
  pending: "bg-amber-500",
  overdue: "bg-red-500",
};

const LABELS = {
  met: "Met",
  pending: "Pending",
  overdue: "Overdue",
};

export default function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${STYLES[status]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${DOT[status]}`} />
      {LABELS[status]}
    </span>
  );
}
