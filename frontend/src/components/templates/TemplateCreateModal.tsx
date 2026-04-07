import {
  Modal,
  TextInput,
  Textarea,
  Select,
  Button,
  Group,
  Stack,
  NumberInput,
  Switch,
  Divider,
  Text,
  Accordion,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { templatesApi, type TemplateCreate } from "../../api/templates";

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function TemplateCreateModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();

  const form = useForm({
    initialValues: {
      name: "",
      description: "",
      sim_type: "aero" as "aero" | "ghn",
      comment: "",
      // simulation_parameter
      inflow_velocity: 38.88,
      density: 1.2041,
      dynamic_viscosity: 0.000018194,
      temperature: 20.0,
      specific_gas_constant: 287.05,
      mach_factor: 2.0,
      num_ramp_up_iter: 200,
      finest_resolution_size: 0.0015,
      number_of_resolution: 7,
      simulation_time: 2.0,
      // setup_option flags
      temperature_degree: true,
      simulation_time_with_FP: false,
      triangle_splitting: true,
      domain_bounding_box_relative: true,
      box_offset_relative: true,
      box_refinement_porous: true,
      moving_ground: true,
      opt_belt_system: true,
      num_belts: 5,
      activate_body_tg: true,
      activate_ground_tg: true,
    },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
      sim_type: (v) => (v ? null : "Type is required"),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: TemplateCreate) => templatesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({ message: "Template created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  function handleSubmit(values: typeof form.values) {
    const payload: TemplateCreate = {
      name: values.name.trim(),
      description: values.description.trim() || undefined,
      sim_type: values.sim_type,
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
              no_slip_static_ground_patch: true,
              ground_zmin_auto: true,
              boundary_layer_suction_position_from_belt_xmin: true,
            },
            belt: {
              opt_belt_system: values.opt_belt_system,
              num_belts: values.num_belts,
              include_wheel_belt_forces: true,
              wheel_belt_location_auto: true,
            },
            turbulence_generator: {
              activate_body_tg: values.activate_body_tg,
              activate_ground_tg: values.activate_ground_tg,
            },
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
          simulation_time_FP: 30,
        },
        setup: {
          domain_bounding_box: [-5, 15, -12, 12, 0, 20],
          meshing: {
            box_refinement: {},
            part_box_refinement: {},
            offset_refinement: {},
            custom_refinement: {},
          },
          boundary_condition_input: {
            belts: {},
            boundary_layer_suction_xpos: -1.1,
          },
        },
        target_names: {
          wheel: [],
          rim: [],
          porous: [],
          car_bounding_box: [],
          baffle: [],
          triangle_splitting: [],
        },
      },
    };
    mutation.mutate(payload);
  }

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="New Template"
      size="lg"
      scrollAreaComponent={Modal.NativeScrollArea}
    >
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack>
          {/* Basic info */}
          <TextInput label="Name" placeholder="e.g. Aero_Standard_2025" required {...form.getInputProps("name")} />
          <Textarea label="Description" placeholder="Optional description" {...form.getInputProps("description")} />
          <Select
            label="Simulation type"
            data={[
              { value: "aero", label: "Aero (External aerodynamics)" },
              { value: "ghn", label: "GHN (Greenhouse noise)" },
            ]}
            required
            {...form.getInputProps("sim_type")}
          />
          <TextInput label="Version comment" placeholder="Initial version" {...form.getInputProps("comment")} />

          <Divider label="Simulation Parameters" labelPosition="center" />

          {/* Simulation parameters */}
          <Group grow>
            <NumberInput label="Inflow velocity (m/s)" decimalScale={2} {...form.getInputProps("inflow_velocity")} />
            <NumberInput label="Temperature (°C)" decimalScale={1} {...form.getInputProps("temperature")} />
          </Group>
          <Group grow>
            <NumberInput label="Density (kg/m³)" decimalScale={4} {...form.getInputProps("density")} />
            <NumberInput label="Dynamic viscosity" decimalScale={8} {...form.getInputProps("dynamic_viscosity")} />
          </Group>
          <Group grow>
            <NumberInput label="Finest resolution (m)" decimalScale={4} {...form.getInputProps("finest_resolution_size")} />
            <NumberInput label="Resolution levels (N)" {...form.getInputProps("number_of_resolution")} />
          </Group>
          <Group grow>
            <NumberInput label="Mach factor" decimalScale={1} {...form.getInputProps("mach_factor")} />
            <NumberInput label="Ramp-up iterations" {...form.getInputProps("num_ramp_up_iter")} />
            <NumberInput label="Simulation time (s)" decimalScale={1} {...form.getInputProps("simulation_time")} />
          </Group>

          <Divider label="Setup Options" labelPosition="center" />

          <Accordion>
            <Accordion.Item value="meshing">
              <Accordion.Control><Text size="sm">Meshing options</Text></Accordion.Control>
              <Accordion.Panel>
                <Stack gap="xs">
                  <Switch label="Triangle splitting" {...form.getInputProps("triangle_splitting", { type: "checkbox" })} />
                  <Switch label="Domain bbox relative to vehicle" {...form.getInputProps("domain_bounding_box_relative", { type: "checkbox" })} />
                  <Switch label="Box/offset sizes relative" {...form.getInputProps("box_offset_relative", { type: "checkbox" })} />
                  <Switch label="Porous box refinement" {...form.getInputProps("box_refinement_porous", { type: "checkbox" })} />
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="bc">
              <Accordion.Control><Text size="sm">Boundary condition options</Text></Accordion.Control>
              <Accordion.Panel>
                <Stack gap="xs">
                  <Switch label="Moving ground" {...form.getInputProps("moving_ground", { type: "checkbox" })} />
                  <Switch label="Belt system" {...form.getInputProps("opt_belt_system", { type: "checkbox" })} />
                  <NumberInput label="Number of belts" {...form.getInputProps("num_belts")} />
                  <Switch label="Activate body turbulence generator" {...form.getInputProps("activate_body_tg", { type: "checkbox" })} />
                  <Switch label="Activate ground turbulence generator" {...form.getInputProps("activate_ground_tg", { type: "checkbox" })} />
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>

          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={mutation.isPending}>Create</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
