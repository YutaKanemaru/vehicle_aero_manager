import {
  AppShell as MantineAppShell,
  Burger,
  Group,
  Title,
  NavLink,
  Button,
  Text,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconTemplate, IconSettings, IconLogout, IconBox, IconStack2 } from "@tabler/icons-react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../stores/auth";

const navItems = [
  { label: "Templates", path: "/templates", icon: IconTemplate },
  { label: "Geometries", path: "/geometries", icon: IconBox },
  { label: "Assemblies", path: "/assemblies", icon: IconStack2 },
  { label: "Configurations", path: "/configurations", icon: IconSettings },
];

export function AppLayout() {
  const [opened, { toggle }] = useDisclosure();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

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
    </MantineAppShell>
  );
}
