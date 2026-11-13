import { useQuery } from "@tanstack/react-query";
import { api, formatPrice } from "../api/client";
import { getUserId } from "../lib/auth";
import type { Order } from "../types";

const TERMINAL = new Set(["confirmed", "cancelled"]);

export function OrdersPage() {
  const userId = getUserId();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["orders", userId],
    queryFn: () => api.get<{ items: Order[] }>(`/orders?user_id=${userId}`),
    refetchInterval: (query) => {
      const orders = query.state.data?.items ?? [];
      return orders.some((o) => !TERMINAL.has(o.status)) ? 1000 : false;
    },
  });

  if (isLoading) return <p className="py-12 text-center text-gray-500">Loading…</p>;
  if (isError) return <p className="py-12 text-center text-red-500">Failed to load orders.</p>;

  const orders = data?.items ?? [];

  if (orders.length === 0) {
    return <p className="py-12 text-center text-gray-500">You have no orders yet.</p>;
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">My orders</h1>
      <ul className="space-y-4">
        {orders.map((order) => (
          <li key={order.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm text-gray-500">{order.id}</span>
              <StatusBadge status={order.status} />
            </div>
            <div className="mt-3 flex items-center justify-between text-sm text-gray-600">
              <span>{order.items.reduce((n, i) => n + i.quantity, 0)} item(s)</span>
              <span className="font-semibold text-gray-900">{formatPrice(order.total_amount)}</span>
            </div>
            <p className="mt-2 text-xs text-gray-400">
              {new Date(order.created_at).toLocaleString()}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    confirmed: "bg-green-100 text-green-700",
    cancelled: "bg-red-100 text-red-700",
    pending: "bg-gray-100 text-gray-600",
    reserving: "bg-amber-100 text-amber-700",
    paying: "bg-amber-100 text-amber-700",
  };
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${styles[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}
