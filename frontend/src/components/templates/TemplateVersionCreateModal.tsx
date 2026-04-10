import {
  Modal,
  TextInput,
  Button,
  Group,
  Stack,
  NumberInput,
  Switch,
  Divider,
  Text,
  Accordion,
  SimpleGrid,
  ScrollArea,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import {
  templatesApi,
  type TemplateResponse,
  type TemplateVersionCreate,
} from "../../api/templates";

interface Props {
  opened: boolean;
  onClose: () => void;
  template: TemplateResponse;
}

function splitList(s: string): string[] {
  return s.split(",").map((v) => v.trim()).filter(Boolean);
}

function joinList(arr: string[] | undefined | null): string {
  return (arr ?? []).join(", ");
}

function defaultValues(template: TemplateResponse) {
  const sp = template.active_version?.settings?.simulation_parameter;
  const so = template.active_version?.settings?.setup_option;
  const setup = template.active_version?.settings?.setup;
  const tn = template.active_version?.settings?.target_names;
  const bbox = setup?.domain_bounding_box ?? [-5, 15, -12, 12, 0, 20];

  return {
    comment: "",
    // simulation_parameter
    inflow_velocity: sp?.inflow_velocity ?? 38.88,
    density: sp?.density ?? 1.2041,
    dynamic_viscosity: sp?.dynamic_viscosity ?? 0.000018194,
    temperature: sp?.temperature ?? 20.0,
    specific_gas_constant: sp?.specific_gas_constant ?? 287.05,
    mach_factor: sp?.mach_factor ?? 2.0,
    num_ramp_up_iter: sp?.num_ramp_up_iter ?? 200,
    finest_resolution_size: sp?.finest_resolution_size ?? 0.0015,
    number_of_resolution: sp?.number_of_resolution ?? 7,
    simulation_time: sp?.simulation_time ?? 2.0,
    simulation_time_FP: sp?.simulation_time_FP ?? 30.0,
    start_averaging_time: sp?.start_averaging_time ?? 1.5,
    avg_window_size: sp?.avg_window_size ?? 0.3,
    output_start_time: (sp?.output_start_time ?? null) as number | null,
    output_interval_time: (sp?.output_interval_time ?? null) as number | null,
    yaw_angle: sp?.yaw_angle ?? 0.0,
    // setup_option.simulation
    temperature_degree: so?.simulation?.temperature_degree ?? true,
    simulation_time_with_FP: so?.simulation?.simulation_time_with_FP ?? false,
    // setup_option.meshing
    triangle_splitting: so?.meshing?.triangle_splitting ?? true,
    domain_bounding_box_relative: so?.meshing?.domain_bounding_box_relative ?? true,
    box_offset_relative: so?.meshing?.box_offset_relative ?? true,
    box_refinement_porous: so?.meshing?.box_refinement_porous ?? true,
    // setup_option.boundary_condition.ground
    moving_ground: so?.boundary_condition?.ground?.moving_ground ?? true,
    no_slip_static_ground_patch:
      so?.boundary_condition?.ground?.no_slip_static_ground_patch ?? true,
    ground_zmin_auto: so?.boundary_condition?.ground?.ground_zmin_auto ?? true,
    boundary_layer_suction_position_from_belt_xmin:
      so?.boundary_condition?.ground
        ?.boundary_layer_suction_position_from_belt_xmin ?? true,
    // setup_option.boundary_condition.belt
    opt_belt_system: so?.boundary_condition?.belt?.opt_belt_system ?? true,
    num_belts: so?.boundary_condition?.belt?.num_belts ?? 5,
    include_wheel_belt_forces:
      so?.boundary_condition?.belt?.include_wheel_belt_forces ?? true,
    wheel_belt_location_auto:
      so?.boundary_condition?.belt?.wheel_belt_location_auto ?? true,
    // setup_option.boundary_condition.turbulence_generator
    activate_body_tg:
      so?.boundary_condition?.turbulence_generator?.activate_body_tg ?? true,
    activate_ground_tg:
      so?.boundary_condition?.turbulence_generator?.activate_ground_tg ?? true,
    // setup_option.compute
    rotate_wheels: so?.compute?.rotate_wheels ?? true,
    porous_media: so?.compute?.porous_media ?? true,
    turbulence_generator_compute: so?.compute?.turbulence_generator ?? true,
    compute_moving_ground: so?.compute?.moving_ground ?? true,
    adjust_ride_height: so?.compute?.adjust_ride_height ?? false,
    // setup.domain_bounding_box
    bbox_xmin: bbox[0] ?? -5.0,
    bbox_xmax: bbox[1] ?? 15.0,
    bbox_ymin: bbox[2] ?? -12.0,
    bbox_ymax: bbox[3] ?? 12.0,
    bbox_zmin: bbox[4] ?? 0.0,
    bbox_zmax: bbox[5] ?? 20.0,
    // setup.boundary_condition_input
    boundary_layer_suction_xpos:
      setup?.boundary_condition_input?.boundary_layer_suction_xpos ?? -1.1,
    // target_names
    tn_wheel: joinList(tn?.wheel),
    tn_rim: joinList(tn?.rim),
    tn_porous: joinList(tn?.porous),
    tn_car_bounding_box: joinList(tn?.car_bounding_box),
    tn_baffle: joinList(tn?.baffle),
    tn_triangle_splitting: joinList(tn?.triangle_splitting),
    tn_windtunnel: joinList(tn?.windtunnel),
    tn_wheel_tire_fr_lh: tn?.wheel_tire_fr_lh ?? "",
    tn_wheel_tire_fr_rh: tn?.wheel_tire_fr_rh ?? "",
    tn_wheel_tire_rr_lh: tn?.wheel_tire_rr_lh ?? "",
    tn_wheel_tire_rr_rh: tn?.wheel_tire_rr_rh ?? "",
    tn_overset_fr_lh: tn?.overset_fr_lh ?? "",
    tn_overset_fr_rh: tn?.overset_fr_rh ?? "",
    tn_overset_rr_lh: tn?.overset_rr_lh ?? "",
    tn_overset_rr_rh: tn?.overset_rr_rh ?? "",
  };
}

export function TemplateVersionCreateModal({ opened, onClose, template }: Props) {
  const queryClient = useQueryClient();

  const form = useForm({ initialValues: defaultValues(template) });

  const mutation = useMutation({
    mutationFn: (data: TemplateVersionCreate) =>
      templatesApi.createVersion(template.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      queryClient.invalidateQueries({
        queryKey: ["templates", template.id, "versions"],
      });
      notifications.show({ message: "New version created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  function buildPayload(values: typeof form.values): TemplateVersionCreate {
    const activeSetup = template.active_version?.settings?.setup;
    return {
      comment: values.comment.trim() || undefined,
      settings: {
        setup_option: {
          simulation: {
            temperature_degree: values.temperature_degree,
            simulation_time_with_FP: values.simulation_time_with_FP,
          },
          meshing: {
            triangle_splitting: values.triangle_splitting,
            domain_bounding_box_relative: values.domain_bounding_box_relative,
            box_offset_relative: values.box_offset_relative,
            box_refinement_porous: values.box_refinement_porous,
          },
          boundary_condition: {
            ground: {
              moving_ground: values.moving_ground,
              no_slip_static_ground_patch: values.no_slip_static_ground_patch,
              ground_zmin_auto: values.ground_zmin_auto,
              boundary_layer_suction_position_from_belt_xmin:
                values.boundary_layer_suction_position_from_belt_xmin,
            },
            belt: {
              opt_belt_system: values.opt_belt_system,
              num_belts: values.num_belts,
              include_wheel_belt_forces: values.include_wheel_belt_forces,
              wheel_belt_location_auto: values.wheel_belt_location_auto,
            },
            turbulence_generator: {
              activate_body_tg: values.activate_body_tg,
              activate_ground_tg: values.activate_ground_tg,
            },
          },
          compute: {
            rotate_wheels: values.rotate_wheels,
            porous_media: values.porous_media,
            turbulence_generator: values.turbulence_generator_compute,
            moving_ground: values.compute_moving_ground,
            adjust_ride_height: values.adjust_ride_height,
          },
        },
        simulation_parameter: {
          inflow_velocity: values.inflow_velocity,
          density: values.density,
          dynamic_viscosity: values.dynamic_viscosity,
          temperature: values.temperature,
          specific_gas_constant: values.specific_gas_constant,
          mach_factor: values.mach_factor,
          num_ramp_up_iter: values.num_ramp_up_iter,
          finest_resolution_size: values.finest_resolution_size,
          number_of_resolution: values.number_of_resolution,
          simulation_time: values.simulation_time,
          simulation_time_FP: values.simulation_time_FP,
          start_averaging_time: values.start_averaging_time,
          avg_window_size: values.avg_window_size,
          output_start_time: values.output_start_time ?? undefined,
          output_interval_time: values.output_interval_time ?? undefined,
          yaw_angle: values.yaw_angle,
        },
        setup: {
          domain_bounding_box: [
            values.bbox_xmin,
            values.bbox_xmax,
            values.bbox_ymin,
            values.bbox_ymax,
            values.bbox_zmin,
            values.bbox_zmax,
          ],
          meshing: activeSetup?.meshing ?? {
            box_refinement: {},
            part_box_refinement: {},
            offset_refinement: {},
            custom_refinement: {},
          },
          boundary_condition_input: {
            belts: activeSetup?.boundary_condition_input?.belts ?? {},
            boundary_layer_suction_xpos: values.boundary_layer_suction_xpos,
          },
        },
        target_names: {
          wheel: splitList(values.tn_wheel),
          rim: splitList(values.tn_rim),
          porous: splitList(values.tn_porous),
          car_bounding_box: splitList(values.tn_car_bounding_box),
          baffle: splitList(values.tn_baffle),
          triangle_splitting: splitList(values.tn_triangle_splitting),
          windtunnel: splitList(values.tn_windtunnel),
          wheel_tire_fr_lh: values.tn_wheel_tire_fr_lh.trim(),
          wheel_tire_fr_rh: values.tn_wheel_tire_fr_rh.trim(),
          wheel_tire_rr_lh: values.tn_wheel_tire_rr_lh.trim(),
          wheel_tire_rr_rh: values.tn_wheel_tire_rr_rh.trim(),
          overset_fr_lh: values.tn_overset_fr_lh.trim(),
          overset_fr_rh: values.tn_overset_fr_rh.trim(),
          overset_rr_lh: values.tn_overset_rr_lh.trim(),
          overset_rr_rh: values.tn_overset_rr_rh.trim(),
        },
      },
    };
  }

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={`New Version — ${template.name}`}
      size="xl"
      scrollAreaComponent={ScrollArea.Autosize}
    >
      <form onSubmit={form.onSubmit((v) => mutation.mutate(buildPayload(v)))}>
        <Stack>
          <TextInput
            label="Version comment"
            placeholder="What changed in this version?"
            {...form.getInputProps("comment")}
          />

          {/* ── Simulation Parameters ──────────────────────────────── */}
          <Divider label="Simulation Parameters" labelPosition="center" />

          <SimpleGrid cols={3}>
            <NumberInput
              label="Inflow velocity (m/s)"
              decimalScale={2}
              {...form.getInputProps("inflow_velocity")}
            />
            <NumberInput
              label="Temperature (°C)"
              decimalScale={1}
              {...form.getInputProps("temperature")}
            />
            <NumberInput
              label="Yaw angle (°)"
              decimalScale={2}
              {...form.getInputProps("yaw_angle")}
            />
          </SimpleGrid>
          <SimpleGrid cols={3}>
            <NumberInput
              label="Density (kg/m³)"
              decimalScale={4}
              {...form.getInputProps("density")}
            />
            <NumberInput
              label="Dynamic viscosity"
              decimalScale={9}
              {...form.getInputProps("dynamic_viscosity")}
            />
            <NumberInput
              label="Specific gas constant (J/kg·K)"
              decimalScale={2}
              {...form.getInputProps("specific_gas_constant")}
            />
          </SimpleGrid>
          <SimpleGrid cols={3}>
            <NumberInput
              label="Finest resolution (m)"
              decimalScale={4}
              {...form.getInputProps("finest_resolution_size")}
            />
            <NumberInput
              label="Resolution levels (N)"
              {...form.getInputProps("number_of_resolution")}
            />
            <NumberInput
              label="Mach factor"
              decimalScale={1}
              {...form.getInputProps("mach_factor")}
            />
          </SimpleGrid>
          <SimpleGrid cols={3}>
            <NumberInput
              label="Simulation time (s)"
              decimalScale={1}
              {...form.getInputProps("simulation_time")}
            />
            <NumberInput
              label="Simulation time — flow passages"
              decimalScale={1}
              {...form.getInputProps("simulation_time_FP")}
            />
            <NumberInput
              label="Ramp-up iterations"
              {...form.getInputProps("num_ramp_up_iter")}
            />
          </SimpleGrid>
          <SimpleGrid cols={4}>
            <NumberInput
              label="Averaging start (s)"
              decimalScale={2}
              {...form.getInputProps("start_averaging_time")}
            />
            <NumberInput
              label="Averaging window (s)"
              decimalScale={2}
              {...form.getInputProps("avg_window_size")}
            />
            <NumberInput
              label="Output start (s, auto)"
              decimalScale={2}
              placeholder="auto"
              allowDecimal
              {...form.getInputProps("output_start_time")}
            />
            <NumberInput
              label="Output interval (s, auto)"
              decimalScale={2}
              placeholder="auto"
              allowDecimal
              {...form.getInputProps("output_interval_time")}
            />
          </SimpleGrid>

          {/* ── Setup Options ──────────────────────────────────────── */}
          <Divider label="Setup Options" labelPosition="center" />

          <Accordion multiple variant="contained">
            <Accordion.Item value="simulation">
              <Accordion.Control>
                <Text size="sm" fw={500}>Simulation options</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Group>
                  <Switch
                    label="Temperature input in °C (converted to K)"
                    {...form.getInputProps("temperature_degree", { type: "checkbox" })}
                  />
                  <Switch
                    label="Use flow-passage time instead of fixed time"
                    {...form.getInputProps("simulation_time_with_FP", { type: "checkbox" })}
                  />
                </Group>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="meshing">
              <Accordion.Control>
                <Text size="sm" fw={500}>Meshing options</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="xs">
                  <Switch
                    label="Triangle splitting"
                    {...form.getInputProps("triangle_splitting", { type: "checkbox" })}
                  />
                  <Switch
                    label="Domain bounding box relative to vehicle"
                    {...form.getInputProps("domain_bounding_box_relative", { type: "checkbox" })}
                  />
                  <Switch
                    label="Box/offset sizes relative"
                    {...form.getInputProps("box_offset_relative", { type: "checkbox" })}
                  />
                  <Switch
                    label="Porous box refinement"
                    {...form.getInputProps("box_refinement_porous", { type: "checkbox" })}
                  />
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="bc">
              <Accordion.Control>
                <Text size="sm" fw={500}>Boundary condition options</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="xs">
                  <Text size="xs" c="dimmed" fw={500}>Ground</Text>
                  <Switch
                    label="Moving ground"
                    {...form.getInputProps("moving_ground", { type: "checkbox" })}
                  />
                  <Switch
                    label="No-slip static ground patch"
                    {...form.getInputProps("no_slip_static_ground_patch", { type: "checkbox" })}
                  />
                  <Switch
                    label="Ground Z-min auto"
                    {...form.getInputProps("ground_zmin_auto", { type: "checkbox" })}
                  />
                  <Switch
                    label="Boundary layer suction position from belt X-min"
                    {...form.getInputProps(
                      "boundary_layer_suction_position_from_belt_xmin",
                      { type: "checkbox" }
                    )}
                  />
                  <Text size="xs" c="dimmed" fw={500} mt="xs">Belt</Text>
                  <Switch
                    label="Belt system"
                    {...form.getInputProps("opt_belt_system", { type: "checkbox" })}
                  />
                  <NumberInput
                    label="Number of belts"
                    {...form.getInputProps("num_belts")}
                    w={120}
                  />
                  <Switch
                    label="Include wheel-belt forces"
                    {...form.getInputProps("include_wheel_belt_forces", { type: "checkbox" })}
                  />
                  <Switch
                    label="Wheel belt location auto"
                    {...form.getInputProps("wheel_belt_location_auto", { type: "checkbox" })}
                  />
                  <Text size="xs" c="dimmed" fw={500} mt="xs">Turbulence generator</Text>
                  <Switch
                    label="Activate body turbulence generator"
                    {...form.getInputProps("activate_body_tg", { type: "checkbox" })}
                  />
                  <Switch
                    label="Activate ground turbulence generator"
                    {...form.getInputProps("activate_ground_tg", { type: "checkbox" })}
                  />
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="compute">
              <Accordion.Control>
                <Text size="sm" fw={500}>
                  Compute options (defaults, overridable per configuration)
                </Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="xs">
                  <Switch
                    label="Rotate wheels (overset + rotating wall BC)"
                    {...form.getInputProps("rotate_wheels", { type: "checkbox" })}
                  />
                  <Switch
                    label="Porous media (porous sources + box refinement)"
                    {...form.getInputProps("porous_media", { type: "checkbox" })}
                  />
                  <Switch
                    label="Turbulence generator (Aero only)"
                    {...form.getInputProps("turbulence_generator_compute", { type: "checkbox" })}
                  />
                  <Switch
                    label="Moving ground (belt BC)"
                    {...form.getInputProps("compute_moving_ground", { type: "checkbox" })}
                  />
                  <Switch
                    label="Adjust ride height"
                    {...form.getInputProps("adjust_ride_height", { type: "checkbox" })}
                  />
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>

          {/* ── Domain Setup ───────────────────────────────────────── */}
          <Divider label="Domain Setup" labelPosition="center" />

          <Text size="sm" c="dimmed">
            Domain bounding box multipliers (relative to vehicle dimensions)
          </Text>
          <SimpleGrid cols={3}>
            <NumberInput
              label="X-min multiplier"
              decimalScale={1}
              {...form.getInputProps("bbox_xmin")}
            />
            <NumberInput
              label="X-max multiplier"
              decimalScale={1}
              {...form.getInputProps("bbox_xmax")}
            />
            <NumberInput
              label="Y-min multiplier"
              decimalScale={1}
              {...form.getInputProps("bbox_ymin")}
            />
            <NumberInput
              label="Y-max multiplier"
              decimalScale={1}
              {...form.getInputProps("bbox_ymax")}
            />
            <NumberInput
              label="Z-min multiplier"
              decimalScale={1}
              {...form.getInputProps("bbox_zmin")}
            />
            <NumberInput
              label="Z-max multiplier"
              decimalScale={1}
              {...form.getInputProps("bbox_zmax")}
            />
          </SimpleGrid>
          <NumberInput
            label="Boundary layer suction X position (m)"
            decimalScale={3}
            w={260}
            {...form.getInputProps("boundary_layer_suction_xpos")}
          />

          {/* ── Target Part Names ──────────────────────────────────── */}
          <Divider label="Target Part Names" labelPosition="center" />
          <Text size="sm" c="dimmed">
            Part-name matching patterns. Separate multiple values with commas.
          </Text>

          <SimpleGrid cols={2}>
            <TextInput
              label="Wheel parts (prefix/substring)"
              placeholder="Wheel_"
              {...form.getInputProps("tn_wheel")}
            />
            <TextInput
              label="Rim parts"
              placeholder="_Spokes_"
              {...form.getInputProps("tn_rim")}
            />
            <TextInput
              label="Porous media parts"
              placeholder="Porous_Media_"
              {...form.getInputProps("tn_porous")}
            />
            <TextInput
              label="Car bounding box parts"
              placeholder=""
              {...form.getInputProps("tn_car_bounding_box")}
            />
            <TextInput
              label="Baffle parts"
              placeholder="_Baffle_"
              {...form.getInputProps("tn_baffle")}
            />
            <TextInput
              label="Triangle splitting parts"
              placeholder=""
              {...form.getInputProps("tn_triangle_splitting")}
            />
            <TextInput
              label="Wind tunnel parts (passive)"
              placeholder=""
              {...form.getInputProps("tn_windtunnel")}
            />
          </SimpleGrid>

          <Text size="sm" c="dimmed" mt="xs">
            Individual tyre part IDs (required for OSM + belt auto-positioning)
          </Text>
          <SimpleGrid cols={2}>
            <TextInput
              label="FR-LH tyre"
              placeholder="Wheel_Tire_FR_LH"
              {...form.getInputProps("tn_wheel_tire_fr_lh")}
            />
            <TextInput
              label="FR-RH tyre"
              placeholder="Wheel_Tire_FR_RH"
              {...form.getInputProps("tn_wheel_tire_fr_rh")}
            />
            <TextInput
              label="RR-LH tyre"
              placeholder="Wheel_Tire_RR_LH"
              {...form.getInputProps("tn_wheel_tire_rr_lh")}
            />
            <TextInput
              label="RR-RH tyre"
              placeholder="Wheel_Tire_RR_RH"
              {...form.getInputProps("tn_wheel_tire_rr_rh")}
            />
          </SimpleGrid>

          <Text size="sm" c="dimmed" mt="xs">
            Overset mesh region part IDs
          </Text>
          <SimpleGrid cols={2}>
            <TextInput
              label="Overset FR-LH"
              placeholder="VREV_OSM_FR_LH"
              {...form.getInputProps("tn_overset_fr_lh")}
            />
            <TextInput
              label="Overset FR-RH"
              placeholder="VREV_OSM_FR_RH"
              {...form.getInputProps("tn_overset_fr_rh")}
            />
            <TextInput
              label="Overset RR-LH"
              placeholder="VREV_OSM_RR_LH"
              {...form.getInputProps("tn_overset_rr_lh")}
            />
            <TextInput
              label="Overset RR-RH"
              placeholder="VREV_OSM_RR_RH"
              {...form.getInputProps("tn_overset_rr_rh")}
            />
          </SimpleGrid>

          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={mutation.isPending}>
              Create Version
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
