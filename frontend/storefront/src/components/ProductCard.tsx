import { Link } from "react-router-dom";
import { formatPrice } from "../api/client";
import { useCart } from "../store/cart";
import type { Product } from "../types";

export function ProductCard({ product }: { product: Product }) {
  const addItem = useCart((s) => s.addItem);
  const open = useCart((s) => s.open);

  return (
    <div className="group flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition hover:shadow-md">
      <Link to={`/product/${product.id}`} className="block aspect-square bg-gray-100">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-400">
            <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.6-4.6a2 2 0 012.8 0L16 16m-2-2l1.6-1.6a2 2 0 012.8 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}
      </Link>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <Link
            to={`/product/${product.id}`}
            className="font-medium text-gray-900 hover:text-brand-600"
          >
            {product.name}
          </Link>
          <span className="whitespace-nowrap font-semibold text-gray-900">
            {formatPrice(product.price)}
          </span>
        </div>
        <p className="text-xs uppercase tracking-wide text-gray-400">{product.category}</p>
        <button
          onClick={() => {
            addItem(product);
            open();
          }}
          className="mt-auto rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          Add to cart
        </button>
      </div>
    </div>
  );
}
