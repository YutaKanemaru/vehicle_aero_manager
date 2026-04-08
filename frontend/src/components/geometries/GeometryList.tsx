import {
  Table,
  Badge,
  Button,
  Group,
  Text,
  Stack,
  ActionIcon,
  Tooltip,
  Collapse,
  Box,
  SimpleGrid,
  ScrollArea,
  NumberFormatter,
} from "@mantine/core";
import {
  IconUpload,
  IconTrash,
  IconChevronDown,
  IconChevronRight,
  IconRefresh,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { useDisclosure } from "@mantine/hooks";
import { geometriesApi, type GeometryResponse } from "../../api/geometries";
import { useAuthStore } from "../../stores/auth";
import { GeometryUploadModal } from "./GeometryUploadModal";

function statusColor(status: string) {
  if (status === "ready") return "green";
  if (status === "error") return "red";
  if (status === "analyzing") return "blue";
  return "yellow";
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function AnalysisDetails({ geometry }: { geometry: GeometryResponse }) {
  const result = geometry.analysis_result;
  if (!result) return <Text size="sm" c="dimmed">No analysis data</Text>;

  const dims = result.vehicle_dimensions;
  const bbox = result.vehicle_bbox;
  const partNames = Object.keys(result.part_info);

  return (
    <Box p="sm" bg="gray.0" style={{ borderRadius: 6 }}>
      <SimpleGrid cols={2} spacing="xs" mb="xs">
        <Box>
          <Text size="xs" c="dimmed">Vehicle bounding box</Text>
          {bbox && (
            <Text size="xs" ff="monospace">
              X [{bbox.x_min.toFixed(3)}, {bbox.x_max.toFixed(3)}]<br />
              Y [{bbox.y_min.toFixed(3)}, {bbox.y_max.toFixed(3)}]<br />
              Z [{bbox.z_min.toFixed(3)}, {bbox.z_max.toFixed(3)}]
            </Text>
          )}
        </Box>
        <Box>
          <Text size="xs" c="dimmed">Dimensions (L × W × H)</Text>
          {dims && (
            <Text size="xs">
              {dims.length.toFixed(3)} m × {dims.width.toFixed(3)} m × {dims.height.toFixed(3)} m
            </Text>
          )}
        </Box>
      </SimpleGrid>
      <Text size="xs" c="dimmed" mb={4}>Parts ({partNames.length})</Text>
      <ScrollArea h={140}>
        <Table fz="xs" withColumnBorders withRowBorders={false}>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Faces</Table.Th>
              <Table.Th>Vertices</Table.Th>
              <Table.Th>Centroid (x, y, z)</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {partNames.map((name) => {
              const p = result.part_info[name];
              return (
                <Table.Tr key={name}>
                  <Table.Td>{name}</Table.Td>
                  <Table.Td><NumberFormatter value={p.face_count} thousandSeparator /></Table.Td>
                  <Table.Td><NumberFormatter value={p.vertex_count} thousandSeparator /></Table.Td>
                  <Table.Td ff="monospace">
                    ({p.centroid[0].toFixed(3)}, {p.centroid[1].toFixed(3)}, {p.centroid[2].toFixed(3)})
                  </Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Tbody>
        </Table>
      </ScrollArea>
    </Box>
  );
}

function GeometryRow({ geometry, canDelete }: { geometry: GeometryResponse; canDelete: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => geometriesApi.delete(geometry.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["geometries"] });
      notifications.show({ message: "Geometry deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const partCount = geometry.analysis_result
    ? Object.keys(geometry.analysis_result.part_info).length
    : null;

  return (
    <>
      <Table.Tr style={{ cursor: "pointer" }} onClick={() => setExpanded((v) => !v)}>
        <Table.Td>
          <Group gap={4}>
            {expanded ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
            <Text size="sm">{geometry.name}</Text>
          </Group>
        </Table.Td>
        <Table.Td>
          <Text size="xs" c="dimmed">{geometry.original_filename}</Text>
        </Table.Td>
        <Table.Td>
          <Text size="sm">{formatBytes(geometry.file_size)}</Text>
        </Table.Td>
        <Table.Td>
          <Badge color={statusColor(geometry.status)} size="sm">
            {geometry.status}
          </Badge>
        </Table.Td>
        <Table.Td>
          <Text size="sm">{partCount !== null ? partCount : "—"}</Text>
        </Table.Td>
        <Table.Td>
          <Text size="xs">{new Date(geometry.created_at).toLocaleDateString()}</Text>
        </Table.Td>
        <Table.Td onClick={(e) => e.stopPropagation()}>
          <Group gap={4} justify="flex-end">
            {canDelete && (
              <Tooltip label="Delete">
                <ActionIcon
                  color="red"
                  variant="subtle"
                  size="sm"
                  loading={deleteMutation.isPending}
                  onClick={() => deleteMutation.mutate()}
                >
                  <IconTrash size={14} />
                </ActionIcon>
              </Tooltip>
            )}
          </Group>
        </Table.Td>
      </Table.Tr>
      {expanded && (
        <Table.Tr>
          <Table.Td colSpan={7} p={0}>
            <Collapse in={expanded}>
              <Box p="sm">
                {geometry.status === "error" && (
                  <Text size="sm" c="red">{geometry.error_message || "Analysis failed"}</Text>
                )}
                {geometry.status === "ready" && <AnalysisDetails geometry={geometry} />}
                {(geometry.status === "pending" || geometry.status === "analyzing") && (
                  <Text size="sm" c="dimmed">Analysis in progress…</Text>
                )}
              </Box>
            </Collapse>
          </Table.Td>
        </Table.Tr>
      )}
    </>
  );
}

export function GeometryList() {
  const user = useAuthStore((s) => s.user);
  const [uploadOpened, { open: openUpload, close: closeUpload }] = useDisclosure(false);

  const { data: geometries = [], isLoading, refetch } = useQuery({
    queryKey: ["geometries"],
    queryFn: geometriesApi.list,
    refetchInterval: (query) => {
      const data = query.state.data as GeometryResponse[] | undefined;
      const hasPending = data?.some((g) => g.status === "pending" || g.status === "analyzing");
      return hasPending ? 3000 : false;
    },
  });

  return (
    <Stack>
      <Group justify="space-between">
        <Text size="xl" fw={600}>Geometries</Text>
        <Group gap="xs">
          <Tooltip label="Refresh">
            <ActionIcon variant="subtle" onClick={() => refetch()} loading={isLoading}>
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          <Button leftSection={<IconUpload size={16} />} onClick={openUpload}>
            Upload STL
          </Button>
        </Group>
      </Group>

      {geometries.length === 0 && !isLoading ? (
        <Text c="dimmed" ta="center" py="xl">No geometries yet. Upload an STL file to get started.</Text>
      ) : (
        <Table highlightOnHover withTableBorder withColumnBorders>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>File</Table.Th>
              <Table.Th>Size</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Parts</Table.Th>
              <Table.Th>Uploaded</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {geometries.map((g) => (
              <GeometryRow
                key={g.id}
                geometry={g}
                canDelete={!!(user && (user.id === g.uploaded_by || user.is_admin))}
              />
            ))}
          </Table.Tbody>
        </Table>
      )}

      <GeometryUploadModal opened={uploadOpened} onClose={closeUpload} />
    </Stack>
  );
}
