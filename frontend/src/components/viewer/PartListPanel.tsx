import {
  Stack,
  TextInput,
  SegmentedControl,
  ScrollArea,
  Group,
  ActionIcon,
  ColorInput,
  Slider,
  Text,
  Button,
  Tooltip,
  Badge,
} from "@mantine/core";
import {
  IconEye,
  IconEyeOff,
  IconSearch,
  IconRefresh,
  IconEyeCheck,
  IconArrowsExchange,
} from "@tabler/icons-react";
import { useViewerStore } from "../../stores/viewerStore";

interface PartListPanelProps {
  parts: string[];
}

// ─── Wildcard pattern matching (parity with backend _matches_pattern) ─────────
// * present  → glob: Body_* = startsWith, *_Body = endsWith, *_Body_* = contains
// * absent   → startsWith OR endsWith (case-insensitive)
function matchesPattern(partName: string, pattern: string): boolean {
  const name = partName.toLowerCase();
  const pat = pattern.toLowerCase();
  if (!pat) return true;
  if (pat.includes("*")) {
    // Escape regex meta chars except *, then replace * with .*
    const escaped = pat.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*");
    return new RegExp(`^${escaped}$`).test(name);
  }
  return name.startsWith(pat) || name.endsWith(pat);
}

export function PartListPanel({ parts }: PartListPanelProps) {
  const {
    partStates,
    setPartState,
    resetParts,
    searchQuery,
    setSearchQuery,
    searchMode,
    setSearchMode,
  } = useViewerStore();

  // 検索フィルタリング（ワイルドカード対応 — バックエンド _matches_pattern と同一ロジック）
  const q = searchQuery.trim();
  const filtered = parts.filter((name) => {
    if (!q) return true;
    const match = matchesPattern(name, q);
    return searchMode === "include" ? match : !match;
  });

  const allVisible = filtered.every((n) => partStates[n]?.visible !== false);

  function toggleAll() {
    const next = !allVisible;
    filtered.forEach((n) => setPartState(n, { visible: next }));
  }

  // Show only filtered parts — hide everything else
  function showOnly() {
    const filteredSet = new Set(filtered);
    parts.forEach((n) => setPartState(n, { visible: filteredSet.has(n) }));
  }

  // Invert visibility of all parts
  function invertAll() {
    parts.forEach((n) => {
      const visible = partStates[n]?.visible !== false;
      setPartState(n, { visible: !visible });
    });
  }

  if (parts.length === 0) {
    return (
      <Text c="dimmed" size="sm" p="xs">
        No parts loaded
      </Text>
    );
  }

  return (
    <Stack gap="xs" style={{ height: "100%", overflow: "hidden" }}>
      {/* Search bar */}
      <TextInput
        size="xs"
        placeholder="Search parts..."
        leftSection={<IconSearch size={14} />}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.currentTarget.value)}
      />

      {/* Include / Exclude toggle */}
      <SegmentedControl
        size="xs"
        value={searchMode}
        onChange={(v) => setSearchMode(v as "include" | "exclude")}
        data={[
          { label: "Include", value: "include" },
          { label: "Exclude", value: "exclude" },
        ]}
        fullWidth
      />

      {/* Toolbar */}
      <Group justify="space-between">
        <Badge variant="light" size="sm">
          {filtered.length} / {parts.length}
        </Badge>
        <Group gap={4}>
          <Tooltip label="Toggle visible (filtered)">
            <ActionIcon size="sm" variant="subtle" onClick={toggleAll}>
              {allVisible ? <IconEyeOff size={14} /> : <IconEye size={14} />}
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Show only filtered (hide others)">
            <ActionIcon size="sm" variant="subtle" onClick={showOnly}>
              <IconEyeCheck size={14} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Invert all visibility">
            <ActionIcon size="sm" variant="subtle" onClick={invertAll}>
              <IconArrowsExchange size={14} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Reset all">
            <ActionIcon size="sm" variant="subtle" onClick={resetParts}>
              <IconRefresh size={14} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      {/* Part list */}
      <ScrollArea style={{ flex: 1 }} type="auto">
        <Stack gap={4}>
          {filtered.map((name) => {
            const state = partStates[name] ?? { visible: true, color: "#88aabb", opacity: 1.0 };
            return (
              <Stack key={name} gap={2} p={4} style={{ borderBottom: "1px solid #2a2a2a" }}>
                <Group justify="space-between" gap={4} wrap="nowrap">
                  <Text size="xs" style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {name}
                  </Text>
                  <ActionIcon
                    size="xs"
                    variant="subtle"
                    onClick={() => setPartState(name, { visible: !state.visible })}
                  >
                    {state.visible ? <IconEye size={12} /> : <IconEyeOff size={12} c="dimmed" />}
                  </ActionIcon>
                </Group>

                <Group gap={4} wrap="nowrap">
                  <ColorInput
                    size="xs"
                    value={state.color}
                    onChange={(c) => setPartState(name, { color: c })}
                    withEyeDropper={false}
                    style={{ flex: 1 }}
                    styles={{ input: { height: 22, minHeight: 22, fontSize: 11 } }}
                  />
                  <Slider
                    size="xs"
                    min={0}
                    max={1}
                    step={0.05}
                    value={state.opacity}
                    onChange={(v) => setPartState(name, { opacity: v })}
                    style={{ flex: 1 }}
                  />
                </Group>
              </Stack>
            );
          })}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}
