import {
  Table,
  Button,
  Group,
  Text,
  Stack,
  ActionIcon,
  Tooltip,
  Badge,
  Drawer,
} from "@mantine/core";
import {
  IconPlus,
  IconTrash,
  IconRefresh,
  IconSettings,
  IconCopy,
  IconArrowsLeftRight,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { useDisclosure } from "@mantine/hooks";
import { casesApi } from "../../api/configurations";
import type { CaseResponse } from "../../api/configurations";
import { useAuthStore } from "../../stores/auth";
import { CaseCreateModal } from "./CaseCreateModal";
import { CaseDuplicateModal } from "./CaseDuplicateModal";
import { CaseCompareModal } from "./CaseCompareModal";
import { RunList } from "../runs/RunList";

export function CaseList() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [selectedCase, setSelectedCase] = useState<CaseResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [duplicateCase, setDuplicateCase] = useState<CaseResponse | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);

  const { data: cases = [], isLoading, refetch } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => casesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Case deleted", color: "green" });
      if (selectedCase) setDrawerOpen(false);
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function openDrawer(c: CaseResponse) {
    setSelectedCase(c);
    setDrawerOpen(true);
  }

  function toggleCompareSelect(id: string) {
    setSelectedForCompare((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : prev.length < 2
        ? [...prev, id]
        : prev
    );
  }

  const canDelete = (c: CaseResponse) =>
    c.created_by === user?.id || user?.is_admin;

  return (
    <Stack>
      <Group justify="space-between">
        <Text size="xl" fw={600}>Cases</Text>
        <Group gap="xs">
          <Tooltip label="Refresh">
            <ActionIcon variant="subtle" onClick={() => refetch()} loading={isLoading}>
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label={compareMode ? "Exit compare mode" : "Compare two cases"}>
            <ActionIcon
              variant={compareMode ? "filled" : "subtle"}
              color="orange"
              onClick={() => { setCompareMode((m) => !m); setSelectedForCompare([]); }}
            >
              <IconArrowsLeftRight size={16} />
            </ActionIcon>
          </Tooltip>
          {compareMode && selectedForCompare.length === 2 && (
            <Button size="xs" color="orange" onClick={() => setCompareOpen(true)}>
              Compare
            </Button>
          )}
          <Button leftSection={<IconPlus size={14} />} onClick={openCreate}>
            New Case
          </Button>
        </Group>
      </Group>

      {cases.length === 0 && !isLoading ? (
        <Text c="dimmed" size="sm">
          No cases yet. Create a case by linking a Template and Assembly.
        </Text>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th style={{ width: 70 }}>#</Table.Th>
              <Table.Th>Name</Table.Th>
              <Table.Th>Template</Table.Th>
              <Table.Th>Assembly</Table.Th>
              <Table.Th>Map</Table.Th>
              <Table.Th style={{ width: 60 }}>Runs</Table.Th>
              <Table.Th style={{ width: 90 }}>Created</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {cases.map((c) => (
              <Table.Tr
                key={c.id}
                style={{
                  cursor: "pointer",
                  background: compareMode && selectedForCompare.includes(c.id)
                    ? "rgba(255,140,0,0.12)"
                    : undefined,
                }}
                onClick={() =>
                  compareMode ? toggleCompareSelect(c.id) : openDrawer(c)
                }
              >
                <Table.Td>
                  <Badge variant="outline" color="gray" size="sm">
                    {c.case_number || "—"}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Text fw={500} size="sm">{c.name}</Text>
                  {c.description && (
                    <Text size="xs" c="dimmed" lineClamp={1}>
                      {c.description}
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>
                  <Badge variant="light" color="violet" size="sm">
                    {c.template_name || c.template_id.slice(0, 8)}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Badge variant="light" color="teal" size="sm">
                    {c.assembly_name || c.assembly_id.slice(0, 8)}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  {c.map_id ? (
                    <Badge variant="dot" color="cyan" size="sm">
                      {c.map_name || c.map_id.slice(0, 8)}
                    </Badge>
                  ) : (
                    <Text size="xs" c="dimmed">—</Text>
                  )}
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{c.run_count ?? 0}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="xs" c="dimmed">
                    {new Date(c.created_at).toLocaleDateString()}
                  </Text>
                </Table.Td>
                <Table.Td onClick={(e) => e.stopPropagation()}>
                  <Group gap="xs" wrap="nowrap">
                    <Tooltip label="Open runs">
                      <ActionIcon
                        size="sm"
                        variant="subtle"
                        color="blue"
                        onClick={() => openDrawer(c)}
                      >
                        <IconSettings size={14} />
                      </ActionIcon>
                    </Tooltip>
                    <Tooltip label="Duplicate">
                      <ActionIcon
                        size="sm"
                        variant="subtle"
                        color="orange"
                        onClick={() => setDuplicateCase(c)}
                      >
                        <IconCopy size={14} />
                      </ActionIcon>
                    </Tooltip>
                    {canDelete(c) && (
                      <Tooltip label="Delete">
                        <ActionIcon
                          size="sm"
                          variant="subtle"
                          color="red"
                          loading={deleteMutation.isPending && deleteMutation.variables === c.id}
                          onClick={() => {
                            if (confirm(`Delete case "${c.name}" and all its runs?`)) {
                              deleteMutation.mutate(c.id);
                            }
                          }}
                        >
                          <IconTrash size={14} />
                        </ActionIcon>
                      </Tooltip>
                    )}
                  </Group>
                </Table.Td>
                        </ActionIcon>
                      </Tooltip>
                    )}
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}

      <CaseCreateModal opened={createOpened} onClose={closeCreate} />

      {compareOpen && selectedForCompare.length === 2 && (
        <CaseCompareModal
          caseIds={selectedForCompare as [string, string]}
          opened={compareOpen}
          onClose={() => setCompareOpen(false)}
        />
      )}

      {duplicateCase && (
        <CaseDuplicateModal
          sourceCase={duplicateCase}
          opened={!!duplicateCase}
          onClose={() => setDuplicateCase(null)}
        />
      )}

      {selectedCase && (
        <Drawer
          opened={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          title={
            <Stack gap={2}>
              <Group gap="xs">
                {selectedCase.case_number && (
                  <Badge variant="outline" color="gray" size="sm">
                    {selectedCase.case_number}
                  </Badge>
                )}
                <Text fw={600}>{selectedCase.name}</Text>
              </Group>
              {selectedCase.description && (
                <Text size="xs" c="dimmed">
                  {selectedCase.description}
                </Text>
              )}
            </Stack>
          }
          position="right"
          size="xl"
        >
          <RunList caseId={selectedCase.id} case={selectedCase} />
        </Drawer>
      )}
    </Stack>
  );
}
