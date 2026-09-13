import "@testing-library/jest-dom/vitest";

class ResizeObserverStub {
  constructor(callback) {
    this.callback = callback;
  }
  observe(target) {
    this.callback?.(
      [
        {
          target,
          contentRect: {
            x: 0,
            y: 0,
            width: target?.offsetWidth || 248,
            height: target?.offsetHeight || 110,
            top: 0,
            left: 0,
            bottom: target?.offsetHeight || 110,
            right: target?.offsetWidth || 248,
          },
        },
      ],
      this,
    );
  }
  unobserve() {}
  disconnect() {}
}

class DOMMatrixStub {
  constructor(init) {
    this.a = 1;
    this.b = 0;
    this.c = 0;
    this.d = 1;
    this.e = 0;
    this.f = 0;
    if (typeof init === "string" && init.includes("scale")) {
      const match = /scale\(([^)]+)\)/.exec(init);
      if (match) {
        const value = Number(match[1]);
        this.a = value;
        this.d = value;
      }
    }
  }
}

globalThis.ResizeObserver = ResizeObserverStub;
globalThis.DOMMatrixReadOnly = DOMMatrixStub;
globalThis.DOMMatrix = DOMMatrixStub;

if (!window.matchMedia) {
  window.matchMedia = (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener() {},
    removeListener() {},
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() {
      return false;
    },
  });
}

HTMLElement.prototype.scrollIntoView = function scrollIntoView() {};
HTMLElement.prototype.hasPointerCapture = function hasPointerCapture() {
  return false;
};
HTMLElement.prototype.setPointerCapture = function setPointerCapture() {};
HTMLElement.prototype.releasePointerCapture = function releasePointerCapture() {};

function isNodeLike(el) {
  const className = el.className?.toString?.() || "";
  return className.includes("hm-node") || className.includes("react-flow__node");
}

Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
  configurable: true,
  get() {
    return isNodeLike(this) ? 248 : 1280;
  },
});
Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
  configurable: true,
  get() {
    return isNodeLike(this) ? 110 : 800;
  },
});

const rectFor = (el) => {
  if (isNodeLike(el)) {
    return { x: 24, y: 24, width: 248, height: 110, top: 24, left: 24, bottom: 134, right: 272 };
  }
  return { x: 0, y: 0, width: 1280, height: 800, top: 0, left: 0, bottom: 800, right: 1280 };
};
HTMLElement.prototype.getBoundingClientRect = function getBoundingClientRect() {
  return { ...rectFor(this), toJSON() { return this; } };
};
Object.defineProperty(HTMLElement.prototype, "clientWidth", {
  configurable: true,
  get() { return isNodeLike(this) ? 248 : 1280; },
});
Object.defineProperty(HTMLElement.prototype, "clientHeight", {
  configurable: true,
  get() { return isNodeLike(this) ? 110 : 800; },
});
