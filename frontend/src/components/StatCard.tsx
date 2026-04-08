type StatCardProps = {
  label: string;
  value: string;
  tone?: "warm" | "cool" | "ink";
};

export function StatCard(props: StatCardProps) {
  return (
    <div className={`stat-card ${props.tone ?? "ink"}`}>
      <span>{props.label}</span>
      <strong>{props.value}</strong>
    </div>
  );
}
