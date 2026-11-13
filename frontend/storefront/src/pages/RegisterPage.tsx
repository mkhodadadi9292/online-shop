import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { setSession } from "../lib/auth";
import { AuthForm } from "./LoginPage";

export function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const user = await api.post<{ id: string }>("/users/auth/register", {
        email,
        password,
        full_name: fullName || null,
      });
      const { access_token } = await api.post<{ access_token: string }>("/users/auth/login", {
        email,
        password,
      });
      setSession(user.id, access_token);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  }

  return (
    <AuthForm
      title="Create account"
      submitLabel="Create account"
      error={error}
      onSubmit={submit}
      footer={
        <p className="text-center text-sm text-gray-500">
          Already have an account?{" "}
          <Link to="/login" className="text-brand-600 hover:underline">
            Sign in
          </Link>
        </p>
      }
    >
      <input
        type="text"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        placeholder="Full name"
        className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm"
      />
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
        className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password (min 8 chars)"
        required
        minLength={8}
        className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm"
      />
    </AuthForm>
  );
}
