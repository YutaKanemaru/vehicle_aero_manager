import { useEffect } from "react";
import {
  Modal,
  Group,
  Text,
  Badge,
  TextInput,
  Textarea,
  Select,
  Stack,
  ScrollArea,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import type { TemplateVersionResponse } from "../../api/templates";
import {
  FORM_DEFAULTS,
  valuesFromSettings,
} from "../../hooks/useTemplateSettingsForm";
import { TemplateSettingsForm } from "./TemplateSettingsForm";

interface Props {
  opened: boolean;
  onClose: () => void;
  version: TemplateVersionResponse;
  templateName: string;
  simType: string;
}

export function TemplateSettingsViewModal({
  opened,
  onClose,
  version,
  templateName,
  simType,
}: Props) {
  const sp = version.settings?.simulation_parameter;
  const so = version.settings?.setup_option;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={
        <Group gap="sm">
          <Text fw={600}>{templateName}</Text>
          <Badge variant="light" color={simType === "aero" ? "blue" : "violet"}>
            {simType.toUpperCase()}
          </Badge>
          <Badge variant="outline" color="gray" size="sm">
            v{version.version_number}
            {version.is_active ? " · Active" : ""}
          </Badge>
        </Group>
      }
      size="90%"
    >
      <Stack>
        <Tabs defaultValue="sim">
          <Tabs.List>
            <Tabs.Tab value="sim">Simulation Parameters</Tabs.Tab>
            <Tabs.Tab value="meshing">Meshing Options</Tabs.Tab>
            <Tabs.Tab value="bc">Boundary Conditions</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="sim" pt="md">
            <SimpleGrid cols={2} spacing="sm">
              <NumberInput
                label="Inflow velocity (m/s)"
                value={sp?.inflow_velocity ?? 0}
                decimalScale={2}
                disabled
              />
              <NumberInput
                label="Temperature (°C)"
                value={sp?.temperature ?? 0}
                decimalScale={1}
                disabled
              />
              <NumberInput
                label="Density (kg/m³)"
                value={sp?.density ?? 0}
                decimalScale={4}
                disabled
              />
              <NumberInput
                label="Dynamic viscosity"
                value={sp?.dynamic_viscosity ?? 0}
                decimalScale={8}
                disabled
              />
              <NumberInput
                label="Coarsest voxel size (m)"
                value={sp?.coarsest_voxel_size ?? 0}
                decimalScale={4}
                disabled
              />
              <NumberInput
                label="Resolution levels (N)"
                value={sp?.number_of_resolution ?? 0}
                disabled
              />
              <NumberInput
                label="Mach factor"
                value={sp?.mach_factor ?? 0}
                decimalScale={1}
                disabled
              />
              <NumberInput
                label="Ramp-up iterations"
                value={sp?.num_ramp_up_iter ?? 0}
                disabled
              />
              <NumberInput
                label="Simulation time (s)"
                value={sp?.simulation_time ?? 0}
                decimalScale={1}
                disabled
              />
              <NumberInput
                label="Specific gas constant (J/kg·K)"
                value={sp?.specific_gas_constant ?? 0}
                decimalScale={2}
                disabled
              />
            </SimpleGrid>
            {version.comment && (
              <Text size="sm" c="dimmed" mt="sm">
                Note: {version.comment}
              </Text>
            )}
          </Tabs.Panel>

          <Tabs.Panel value="meshing" pt="md">
            <Stack gap="xs">
              <Switch
                label="Triangle splitting"
                checked={so?.meshing?.triangle_splitting ?? false}
                disabled
              />
              <Switch
                label="Domain bbox relative to vehicle"
                checked={so?.meshing?.domain_bounding_box_relative ?? false}
                disabled
              />
              <Switch
                label="Box/offset sizes relative"
                checked={so?.meshing?.box_offset_relative ?? false}
                disabled
              />
              <Switch
                label="Porous box refinement"
                checked={so?.meshing?.box_refinement_porous ?? false}
                disabled
              />
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="bc" pt="md">
            <Stack gap="xs">
              <Switch
                label="Moving ground"
                checked={(so?.boundary_condition?.ground?.ground_mode ?? "static") !== "static"}
                disabled
              />
              <Switch
                label="Overset wheels"
                checked={so?.boundary_condition?.ground?.overset_wheels ?? false}
                disabled
              />
              <NumberInput
                label="Ground height offset (m)"
                value={so?.boundary_condition?.ground?.ground_height_offset_from_geom_zMin ?? 0}
                decimalScale={4}
                disabled
              />
              <Switch
                label="Body turbulence generator"
                checked={so?.boundary_condition?.turbulence_generator?.enable_body_tg ?? false}
                disabled
              />
              <Switch
                label="Ground turbulence generator"
                checked={so?.boundary_condition?.turbulence_generator?.enable_ground_tg ?? false}
                disabled
              />
            </Stack>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Modal>
  );
}
