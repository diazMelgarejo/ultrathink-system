import type { ReactNode } from "react";

export interface TableColumn<T> {
  key: string;
  header: string;
  width?: string;
  align?: "left" | "right" | "center";
  render: (row: T) => ReactNode;
  mono?: boolean;
}

interface TableProps<T> {
  columns: TableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  empty?: ReactNode;
  className?: string;
  dense?: boolean;
}

export function Table<T>({
  columns,
  rows,
  rowKey,
  empty = "No rows.",
  className = "",
  dense = true,
}: TableProps<T>) {
  if (rows.length === 0) {
    return (
      <div className="rounded border border-line bg-canvas-surface px-4 py-8 text-center text-sm text-ink-muted">
        {empty}
      </div>
    );
  }

  const cellPad = dense ? "px-3 py-1.5" : "px-4 py-3";

  return (
    <div className={`overflow-auto rounded border border-line bg-canvas-surface ${className}`}>
      <table className="w-full border-collapse text-sm">
        <thead className="sticky top-0 z-10 bg-canvas-raised">
          <tr className="border-b border-line">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`${cellPad} text-${col.align ?? "left"} text-2xs font-mono uppercase tracking-wider text-ink-subtle`}
                style={col.width ? { width: col.width } : undefined}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              className="border-b border-line last:border-b-0 hover:bg-canvas-raised/60"
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`${cellPad} text-${col.align ?? "left"} ${col.mono ? "font-mono text-xs" : ""}`}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
