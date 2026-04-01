import { create } from "zustand";

interface User {
  id: string;
  email: string;
  username: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("vam_token"),
  user: null,
  setAuth: (token, user) => {
    localStorage.setItem("vam_token", token);
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem("vam_token");
    set({ token: null, user: null });
  },
}));
