import {
  Modal,
  Stack,
  Group,
  NumberInput,
  Switch,
  Divider,
  Text,
  Accordion,
  Badge,
  SimpleGrid,
} from "@mantine/core";
import type { TemplateVersionResponse } from "../../api/templates";

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
      size="lg"
    >
      <Stack>
        <Divider label="Simulation Parameters" labelPosition="center" />

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
            label="Finest resolution (m)"
            value={sp?.finest_resolution_size ?? 0}
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

        <Divider label="Setup Options" labelPosition="center" />

        <Accordion>
          <Accordion.Item value="meshing">
            <Accordion.Control>
              <Text size="sm">Meshing options</Text>
            </Accordion.Control>
            <Accordion.Panel>
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
            </Accordion.Panel>
          </Accordion.Item>

          <Accordion.Item value="bc">
            <Accordion.Control>
              <Text size="sm">Boundary condition options</Text>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="xs">
                <Switch
                  label="Moving ground"
                  checked={so?.boundary_condition?.ground?.moving_ground ?? false}
                  disabled
                />
                <Switch
                  label="Belt system"
                  checked={so?.boundary_condition?.belt?.opt_belt_system ?? false}
                  disabled
                />
                <NumberInput
                  label="Number of belts"
                  value={so?.boundary_condition?.belt?.num_belts ?? 0}
                  disabled
                />
                <Switch
                  label="Body turbulence generator"
                  checked={
                    so?.boundary_condition?.turbulence_generator?.activate_body_tg ?? false
                  }
                  disabled
                />
                <Switch
                  label="Ground turbulence generator"
                  checked={
                    so?.boundary_condition?.turbulence_generator?.activate_ground_tg ?? false
                  }
                  disabled
                />
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>

        {version.comment && (
          <Text size="sm" c="dimmed">
            Note: {version.comment}
          </Text>
        )}
      </Stack>
    </Modal>
  );
}
