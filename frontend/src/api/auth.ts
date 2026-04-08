import { api } from "./client";

interface LoginRequest {
  username: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  is_admin: boolean;
  is_superadmin: boolean;
}

export const authApi = {
  login: (data: LoginRequest) => api.post<TokenResponse>("/auth/login", data),
  register: (data: RegisterRequest) => api.post<UserResponse>("/auth/register", data),
  me: () => api.get<UserResponse>("/auth/me"),
};
