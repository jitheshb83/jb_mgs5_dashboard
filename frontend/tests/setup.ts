import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});

// recharts' <ResponsiveContainer> measures its DOM node via ResizeObserver
// and getBoundingClientRect, neither of which jsdom implements with a
// non-zero size by default -- without these stubs every chart renders at
// 0x0 in tests. Scoped here (not per-test) since any chart test needs it.
if (typeof globalThis.ResizeObserver === "undefined") {
  class ResizeObserverStub {
    #callback: ResizeObserverCallback;
    constructor(callback: ResizeObserverCallback) {
      this.#callback = callback;
    }
    observe(target: Element) {
      this.#callback(
        [{ target, contentRect: target.getBoundingClientRect() } as ResizeObserverEntry],
        this as unknown as ResizeObserver,
      );
    }
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
}

HTMLElement.prototype.getBoundingClientRect = () =>
  ({
    width: 400,
    height: 240,
    top: 0,
    left: 0,
    right: 400,
    bottom: 240,
    x: 0,
    y: 0,
    toJSON() {},
  }) as DOMRect;
