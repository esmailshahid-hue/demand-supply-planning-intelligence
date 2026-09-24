import { type ReactNode, useState } from 'react';

export default function LazyDetails({
  children,
  className,
  summary,
}: {
  children: ReactNode;
  className?: string;
  summary: ReactNode;
}) {
  const [opened, setOpened] = useState(false);

  return (
    <details
      className={className}
      onToggle={event => {
        if (event.currentTarget.open) setOpened(true);
      }}
    >
      <summary>{summary}</summary>
      {opened ? children : null}
    </details>
  );
}

export function MoreRows({
  count,
  shown,
  label,
  onMore,
  onAll,
}: {
  count: number;
  shown: number;
  label: string;
  onMore: () => void;
  onAll: () => void;
}) {
  if (shown >= count) return <p className="dataset-context">Showing all {count} {label}.</p>;

  return (
    <p className="dataset-context">
      Showing {shown} of {count} {label}.{' '}
      <button onClick={onMore}>Show more</button>{' '}
      <button onClick={onAll}>Show all</button>
    </p>
  );
}
