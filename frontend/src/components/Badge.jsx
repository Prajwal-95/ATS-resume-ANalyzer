const styles = {
  good: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  problem: "bg-red-100 text-red-700",
  excellent: "bg-emerald-100 text-emerald-700",
  matched: "bg-emerald-100 text-emerald-700",
  missing: "bg-red-100 text-red-700",
  additional: "bg-blue-100 text-blue-700",
};

export default function Badge({ status, children }) {
  const className = styles[status] || "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}>
      {children}
    </span>
  );
}
