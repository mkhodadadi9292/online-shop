import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { setSession } from "../lib/auth";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const { access_token } = await api.post<{ access_token: string }>("/users/auth/login", {
        email,
        password,
      });
      setSession(email, access_token);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <AuthForm
      title="Sign in"
      submitLabel="Sign in"
      error={error}
      onSubmit={submit}
      footer={
        <p className="text-center text-sm text-gray-500">
          No account?{" "}
          <Link to="/register" className="text-brand-600 hover:underline">
            Create one
          </Link>
        </p>
      }
    >
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
        placeholder="Password"
        required
        className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm"
      />
    </AuthForm>
  );
}

export function AuthForm({
  title,
  submitLabel,
  error,
  onSubmit,
  footer,
  children,
}: {
  title: string;
  submitLabel: string;
  error: string | null;
  onSubmit: (e: React.FormEvent) => void;
  footer?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-6 text-2xl font-bold">{title}</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        {children}
        {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          className="rounded-lg bg-brand-600 px-4 py-3 font-semibold text-white hover:bg-brand-700"
        >
          {submitLabel}
        </button>
      </form>
      {footer && <div className="mt-6">{footer}</div>}
    </div>
  );
}
