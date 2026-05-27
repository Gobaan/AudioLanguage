import type { ProgressMetric } from './types';

type ProgressCardProps = {
  title?: string;
  metrics?: ProgressMetric[];
  ariaLabel?: string;
};

export function ProgressCard({
  title = 'Progress',
  metrics = [],
  ariaLabel = title,
}: ProgressCardProps) {
  return (
    <section className="progress-card" aria-label={ariaLabel}>
      <h2>{title}</h2>
      <ul>
        {metrics.map((metric) => (
          <li key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </li>
        ))}
      </ul>
    </section>
  );
}
