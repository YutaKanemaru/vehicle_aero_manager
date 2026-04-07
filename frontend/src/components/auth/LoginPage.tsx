import { useState } from "react";
import {
  TextInput,
  PasswordInput,
  Button,
  Paper,
  Title,
  Text,
  Stack,
  Anchor,
  Center,
  Container,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { authApi } from "../../api/auth";
import { useAuthStore } from "../../stores/auth";

export function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);

  const form = useForm({
    initialValues: { email: "", username: "", password: "" },
    validate: {
      username: (v) => (v.length < 2 ? "Username too short" : null),
      password: (v) => (v.length < 6 ? "Password must be at least 6 characters" : null),
      email: (v) =>
        isRegister && !/^\S+@\S+$/.test(v) ? "Invalid email" : null,
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setLoading(true);
    try {
      if (isRegister) {
        await authApi.register(values);
        notifications.show({
          title: "Account created",
          message: "You can now log in",
          color: "green",
        });
        setIsRegister(false);
        return;
      }

      const { access_token } = await authApi.login({
        username: values.username,
        password: values.password,
      });
      // me() を呼ぶ前にトークンを localStorage に保存する
      localStorage.setItem("vam_token", access_token);
      const user = await authApi.me();
      setAuth(access_token, user);
    } catch (e) {
      notifications.show({
        title: "Error",
        message: e instanceof Error ? e.message : "Something went wrong",
        color: "red",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Center h="100vh">
      <Container size={420}>
        <Title ta="center">VAM</Title>
        <Text c="dimmed" size="sm" ta="center" mt={5}>
          Vehicle Aero Manager
        </Text>

        <Paper withBorder shadow="md" p={30} mt={30} radius="md">
          <form onSubmit={form.onSubmit(handleSubmit)}>
            <Stack>
              {isRegister && (
                <TextInput
                  label="Email"
                  placeholder="you@example.com"
                  {...form.getInputProps("email")}
                />
              )}
              <TextInput
                label="Username"
                placeholder="Your username"
                {...form.getInputProps("username")}
              />
              <PasswordInput
                label="Password"
                placeholder="Your password"
                {...form.getInputProps("password")}
              />
              <Button type="submit" fullWidth loading={loading}>
                {isRegister ? "Create account" : "Sign in"}
              </Button>
            </Stack>
          </form>
          <Text c="dimmed" size="sm" ta="center" mt="md">
            {isRegister ? "Already have an account? " : "Don't have an account? "}
            <Anchor
              component="button"
              size="sm"
              onClick={() => setIsRegister(!isRegister)}
            >
              {isRegister ? "Sign in" : "Create account"}
            </Anchor>
          </Text>
        </Paper>
      </Container>
    </Center>
  );
}
