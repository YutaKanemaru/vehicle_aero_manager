import { useMemo, useState } from "react";

export type SortKey = "name" | "created_at";
export type SortDirection = "asc" | "desc";

export interface SortState {
  key: SortKey;
  dir: SortDirection;
}

/** Sort a list of items by name or created_at within a folder section. */
export function useSortedItems<T extends Record<string, unknown>>(items: T[]): {
  sorted: T[];
  sort: SortState;
  toggle: (key: SortKey) => void;
} {
  const [sort, setSort] = useState<SortState>({ key: "name", dir: "asc" });

  const sorted = useMemo(() => {
    return [...items].sort((a, b) => {
      let va: string, vb: string;
      if (sort.key === "created_at") {
        va = String(a["created_at"] ?? "");
        vb = String(b["created_at"] ?? "");
      } else {
        va = String(a["name"] ?? "").toLowerCase();
        vb = String(b["name"] ?? "").toLowerCase();
      }
      const cmp = va < vb ? -1 : va > vb ? 1 : 0;
      return sort.dir === "asc" ? cmp : -cmp;
    });
  }, [items, sort]);

  function toggle(key: SortKey) {
    setSort((prev) =>
      prev.key === key
        ? { key, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { key, dir: "asc" }
    );
  }

  return { sorted, sort, toggle };
}
