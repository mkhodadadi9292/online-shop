import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api, formatPrice } from "../api/client";
import { useCart } from "../store/cart";
import type { Product } from "../types";

export function ProductPage() {
  const { id } = useParams<{ id: string }>();
  const [quantity, setQuantity] = useState(1);
  const addItem = useCart((s) => s.addItem);
  const open = useCart((s) => s.open);

  const { data: product, isLoading, isError } = useQuery({
    queryKey: ["product", id],
    queryFn: () => api.get<Product>(`/products/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <p className="py-12 text-center text-gray-500">Loading…</p>;
  if (isError || !product) return <p className="py-12 text-center text-red-500">Product not found.</p>;

  return (
    <div className="mx-auto max-w-5xl">
      <Link to="/" className="text-sm text-brand-600 hover:underline">
        ← Back to shop
      </Link>

      <div className="mt-6 grid grid-cols-1 gap-8 md:grid-cols-2">
        <div className="aspect-square rounded-2xl bg-gray-100">
          {product.image_url ? (
            <img src={product.image_url} alt={product.name} className="h-full w-full rounded-2xl object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-400">
              <svg className="h-24 w-24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4 16l4.6-4.6a2 2 0 012.8 0L16 16m-2-2l1.6-1.6a2 2 0 012.8 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-4">
          <p className="text-sm uppercase tracking-wide text-gray-400">{product.category}</p>
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="text-2xl font-semibold">{formatPrice(product.price)}</p>
          <p className="text-gray-600">{product.description}</p>

          <div className="mt-4 flex items-center gap-4">
            <div className="flex items-center rounded-lg border border-gray-300">
              <button
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="px-4 py-2 text-gray-600"
              >
                −
              </button>
              <span className="w-10 text-center">{quantity}</span>
              <button
                onClick={() => setQuantity((q) => q + 1)}
                className="px-4 py-2 text-gray-600"
              >
                +
              </button>
            </div>
            <button
              onClick={() => {
                addItem(product, quantity);
                open();
              }}
              className="flex-1 rounded-lg bg-brand-600 px-6 py-3 font-semibold text-white hover:bg-brand-700"
            >
              Add to cart
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
