import {
  Stack,
  TextInput,
  SegmentedControl,
  ScrollArea,
  Group,
  ActionIcon,
  ColorPicker,
  ColorSwatch,
  Slider,
  Text,
  Tooltip,
  Badge,
  Popover,
  Button,
} from "@mantine/core";
import {
  IconEye,
  IconEyeOff,
  IconSearch,
  IconEyeCheck,
  IconArrowsExchange,
  IconFocusCentered,
} from "@tabler/icons-react";
import { useViewerStore } from "../../stores/viewerStore";

interface PartBbox {
  x_min: number; x_max: number;
  y_min: number; y_max: number;
  z_min: number; z_max: number;
}

interface PartListPanelProps {
  parts: string[];
  partInfo?: Record<string, unknown> | null;
}
// 96-color swatch palette: 12 hues × 8 lightness levels
const SWATCHES: string[] = (() => {
  const hues = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];
  const lightness = [15, 25, 35, 45, 58, 68, 78, 88];
  const colors: string[] = [];
  for (const l of lightness) {
    for (const h of hues) {
      colors.push(`hsl(${h}, 75%, ${l}%)`);
    }
  }
  return colors;
})();
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

export function PartListPanel({ parts, partInfo }: PartListPanelProps) {
  const {
    partStates,
    setPartState,
    searchQuery,
    setSearchQuery,
    searchMode,
    setSearchMode,
    selectedPartName,
    setSelectedPartName,
    setFitToTarget,
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
          <Tooltip label="Show all parts">
            <ActionIcon size="sm" variant="subtle" onClick={() => parts.forEach((n) => setPartState(n, { visible: true }))}>
              <IconEye size={14} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      {/* Part list */}
      <ScrollArea style={{ flex: 1 }} type="auto">
        <Stack gap={4}>
          {filtered.map((name) => {
            const state = partStates[name] ?? { visible: true, color: "#88aabb", opacity: 1.0 };
            const isSelected = selectedPartName === name;
            const bbox = (partInfo?.[name] as { bbox?: PartBbox } | undefined)?.bbox;
            function handleFitTo() {
              if (!bbox) return;
              const cx = (bbox.x_min + bbox.x_max) / 2;
              const cy = (bbox.y_min + bbox.y_max) / 2;
              const cz = (bbox.z_min + bbox.z_max) / 2;
              const r = Math.max(
                bbox.x_max - bbox.x_min,
                bbox.y_max - bbox.y_min,
                bbox.z_max - bbox.z_min
              ) * 0.75;
              setFitToTarget({ center: [cx, cy, cz], radius: r });
            }
            return (
              <Stack
                key={name}
                gap={2}
                p={4}
                style={{
                  borderTop: "1px solid #2a2a2a",
                  borderBottom: "1px solid #2a2a2a",
                  background: isSelected ? "rgba(255,255,0,0.1)" : undefined,
                  cursor: "pointer",
                }}
              >
                <Group justify="space-between" gap={4} wrap="nowrap">
                  <Text
                    size="sm"
                    style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    onClick={() => setSelectedPartName(isSelected ? null : name)}
                  >
                    {name}
                  </Text>
                  {bbox && (
                    <Tooltip label="Fit to part">
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        onClick={handleFitTo}
                      >
                        <IconFocusCentered size={12} />
                      </ActionIcon>
                    </Tooltip>
                  )}
                  <Tooltip label="Show only this part">
                    <ActionIcon
                      size="xs"
                      variant="subtle"
                      onClick={() => parts.forEach((n) => setPartState(n, { visible: n === name }))}
                    >
                      <IconEyeCheck size={12} />
                    </ActionIcon>
                  </Tooltip>
                  <ActionIcon
                    size="xs"
                    variant="subtle"
                    onClick={() => setPartState(name, { visible: !state.visible })}
                  >
                    {state.visible ? <IconEye size={12} /> : <IconEyeOff size={12} />}
                  </ActionIcon>
                </Group>

                <Group gap={4} wrap="nowrap">
                  <Popover withArrow position="right-start" withinPortal width="auto">
                    <Popover.Target>
                      <ColorSwatch
                        color={state.color}
                        size={22}
                        style={{ cursor: "pointer", flexShrink: 0, borderRadius: 4 }}
                      />
                    </Popover.Target>
                    <Popover.Dropdown p={6}>
                      <ColorPicker
                        format="hex"
                        value={state.color}
                        onChange={(c) => setPartState(name, { color: c })}
                        withPicker={false}
                        swatches={SWATCHES}
                        swatchesPerRow={12}
                      />
                    </Popover.Dropdown>
                  </Popover>
                  <Popover withArrow position="bottom-start" width={150} withinPortal>
                    <Popover.Target>
                      <Button
                        size="xs"
                        variant="subtle"
                        style={{ fontSize: 10, minWidth: 44, padding: "0 6px", height: 22 }}
                      >
                        α {Math.round(state.opacity * 100)}%
                      </Button>
                    </Popover.Target>
                    <Popover.Dropdown p={8}>
                      <Slider
                        size="xs"
                        min={0}
                        max={1}
                        step={0.05}
                        value={state.opacity}
                        onChange={(v) => setPartState(name, { opacity: v })}
                        style={{ width: 120 }}
                      />
                    </Popover.Dropdown>
                  </Popover>
                </Group>
              </Stack>
            );
          })}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}
