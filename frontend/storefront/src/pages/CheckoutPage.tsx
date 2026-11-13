import { useState } from "react";
import { Link } from "react-router-dom";
import { api, formatPrice } from "../api/client";
import { getUserId } from "../lib/auth";
import { cartTotal, useCart } from "../store/cart";
import type { Order } from "../types";

export function CheckoutPage() {
  const items = useCart((s) => s.items);
  const clear = useCart((s) => s.clear);
  const [placing, setPlacing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [placed, setPlaced] = useState<Order | null>(null);

  async function placeOrder() {
    setPlacing(true);
    setError(null);
    try {
      const order = await api.post<Order>("/orders", {
        user_id: getUserId(),
        items: items.map((i) => ({ product_id: i.product.id, quantity: i.quantity })),
      });
      clear();
      setPlaced(order);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to place order");
    } finally {
      setPlacing(false);
    }
  }

  if (placed) {
    return (
      <div className="mx-auto max-w-lg rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
          <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="mt-4 text-xl font-semibold">Order placed!</h1>
        <p className="mt-2 text-sm text-gray-500">
          Order <span className="font-mono">{placed.id}</span> is{" "}
          <span className="font-medium text-gray-700">{placed.status}</span>.
        </p>
        <Link
          to="/orders"
          className="mt-6 inline-block rounded-lg bg-brand-600 px-6 py-3 font-semibold text-white hover:bg-brand-700"
        >
          View my orders
        </Link>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="text-gray-500">Your cart is empty.</p>
        <Link to="/" className="mt-4 inline-block text-brand-600 hover:underline">
          Continue shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold">Checkout</h1>
      <ul className="divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {items.map((i) => (
          <li key={i.product.id} className="flex justify-between px-5 py-4">
            <div>
              <p className="font-medium">{i.product.name}</p>
              <p className="text-sm text-gray-500">Qty {i.quantity}</p>
            </div>
            <span className="font-medium">{formatPrice(i.product.price * i.quantity)}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6 flex items-center justify-between text-lg font-semibold">
        <span>Total</span>
        <span>{formatPrice(cartTotal(items))}</span>
      </div>

      {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      <button
        onClick={placeOrder}
        disabled={placing}
        className="mt-6 w-full rounded-lg bg-brand-600 px-6 py-3 font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
      >
        {placing ? "Placing order…" : "Place order"}
      </button>
    </div>
  );
}
