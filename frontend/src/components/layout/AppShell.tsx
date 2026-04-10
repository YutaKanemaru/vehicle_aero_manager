import {
  AppShell as MantineAppShell,
  Burger,
  Group,
  Title,
  NavLink,
  Button,
  Text,
  ActionIcon,
  Indicator,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconTemplate, IconLogout, IconBox, IconStack2, IconActivity, IconCar, IconMap } from "@tabler/icons-react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../stores/auth";
import { useJobsStore, selectActiveCount } from "../../stores/jobs";
import { useJobsPoller } from "../../hooks/useJobsPoller";
import { JobsDrawer } from "./JobsDrawer";

const navItems = [
  { label: "Templates", path: "/templates", icon: IconTemplate },
  { label: "Geometries", path: "/geometries", icon: IconBox },
  { label: "Assemblies", path: "/assemblies", icon: IconStack2 },
  { label: "Maps", path: "/maps", icon: IconMap },
  { label: "Cases", path: "/cases", icon: IconCar },
];

export function AppLayout() {
  const [opened, { toggle }] = useDisclosure();
  const [jobsOpen, { open: openJobs, close: closeJobs }] = useDisclosure();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const activeCount = useJobsStore(selectActiveCount);

  useJobsPoller();

  return (
    <MantineAppShell
      header={{ height: 50 }}
      navbar={{ width: 220, breakpoint: "sm", collapsed: { mobile: !opened } }}
      padding="md"
    >
      <MantineAppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Title order={4}>VAM</Title>
          </Group>
          <Group>
            <Text size="sm" c="dimmed">
              {user?.username}
            </Text>
            <Indicator
              label={activeCount > 0 ? activeCount : undefined}
              size={16}
              disabled={activeCount === 0}
              color="blue"
              processing={activeCount > 0}
            >
              <ActionIcon
                variant="subtle"
                size="md"
                onClick={openJobs}
                title="Background Jobs"
              >
                <IconActivity size={18} />
              </ActionIcon>
            </Indicator>
            <Button
              variant="subtle"
              size="xs"
              leftSection={<IconLogout size={16} />}
              onClick={logout}
            >
              Logout
            </Button>
          </Group>
        </Group>
      </MantineAppShell.Header>

      <MantineAppShell.Navbar p="xs">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            label={item.label}
            leftSection={<item.icon size={18} />}
            active={location.pathname.startsWith(item.path)}
            onClick={() => navigate(item.path)}
          />
        ))}
      </MantineAppShell.Navbar>

      <MantineAppShell.Main>
        <Outlet />
      </MantineAppShell.Main>

      <JobsDrawer opened={jobsOpen} onClose={closeJobs} />
    </MantineAppShell>
  );
}
