import { describe, expect, it } from "vitest";
import { cartCount, cartTotal, useCart } from "./cart";
import type { Product } from "../types";

const product: Product = {
  id: "p1",
  name: "Widget",
  description: "A widget",
  price: 1000,
  category: "tools",
  image_url: null,
  created_at: new Date().toISOString(),
};

describe("cart store", () => {
  it("adds items and computes totals", () => {
    useCart.getState().clear();
    useCart.getState().addItem(product, 2);
    useCart.getState().addItem(product, 1);

    const items = useCart.getState().items;
    expect(items).toHaveLength(1);
    expect(items[0].quantity).toBe(3);
    expect(cartCount(items)).toBe(3);
    expect(cartTotal(items)).toBe(3000);
  });

  it("removes items", () => {
    useCart.getState().clear();
    useCart.getState().addItem(product, 1);
    useCart.getState().removeItem("p1");
    expect(useCart.getState().items).toHaveLength(0);
  });
});
