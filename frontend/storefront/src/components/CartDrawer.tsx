import { Link } from "react-router-dom";
import { formatPrice } from "../api/client";
import { cartTotal, useCart } from "../store/cart";

export function CartDrawer() {
  const items = useCart((s) => s.items);
  const isOpen = useCart((s) => s.isOpen);
  const close = useCart((s) => s.close);
  const setQuantity = useCart((s) => s.setQuantity);
  const removeItem = useCart((s) => s.removeItem);

  if (!isOpen) return null;

  return (
    <div className="relative z-30">
      <div className="fixed inset-0 bg-black/30" onClick={close} aria-hidden />
      <div className="fixed inset-y-0 right-0 flex w-full max-w-md flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <h2 className="text-lg font-semibold">Your cart</h2>
          <button onClick={close} className="rounded p-1 text-gray-400 hover:text-gray-700">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {items.length === 0 ? (
            <p className="mt-8 text-center text-gray-500">Your cart is empty.</p>
          ) : (
            <ul className="space-y-4">
              {items.map((item) => (
                <li key={item.product.id} className="flex gap-4">
                  <div className="h-16 w-16 flex-shrink-0 rounded-lg bg-gray-100" />
                  <div className="flex flex-1 flex-col">
                    <div className="flex justify-between gap-2">
                      <span className="font-medium text-gray-900">{item.product.name}</span>
                      <span className="text-gray-700">{formatPrice(item.product.price * item.quantity)}</span>
                    </div>
                    <div className="mt-1 flex items-center gap-2">
                      <button
                        onClick={() => setQuantity(item.product.id, item.quantity - 1)}
                        className="h-7 w-7 rounded border border-gray-300 text-gray-600"
                      >
                        −
                      </button>
                      <span className="w-8 text-center text-sm">{item.quantity}</span>
                      <button
                        onClick={() => setQuantity(item.product.id, item.quantity + 1)}
                        className="h-7 w-7 rounded border border-gray-300 text-gray-600"
                      >
                        +
                      </button>
                      <button
                        onClick={() => removeItem(item.product.id)}
                        className="ml-auto text-sm text-red-500 hover:text-red-600"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {items.length > 0 && (
          <div className="border-t border-gray-200 px-5 py-4">
            <div className="flex justify-between text-base font-semibold">
              <span>Subtotal</span>
              <span>{formatPrice(cartTotal(items))}</span>
            </div>
            <Link
              to="/checkout"
              onClick={close}
              className="mt-4 block rounded-lg bg-brand-600 px-4 py-3 text-center font-semibold text-white hover:bg-brand-700"
            >
              Checkout
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
