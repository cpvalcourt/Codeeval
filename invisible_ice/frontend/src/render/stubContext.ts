/**
 * A recording stub of CanvasRenderingContext2D for unit tests: captures
 * every method call and property write so draw functions can be asserted
 * on without a real canvas.
 */

export interface RecordedCall {
  method: string;
  args: unknown[];
}

export function makeStubContext(): {
  ctx: CanvasRenderingContext2D;
  calls: RecordedCall[];
  count(method: string): number;
} {
  const calls: RecordedCall[] = [];
  const record =
    (method: string) =>
    (...args: unknown[]) => {
      calls.push({ method, args });
    };

  const target: Record<string, unknown> = {};
  const proxy = new Proxy(target, {
    get(t, prop: string) {
      if (prop in t) return t[prop];
      const fn = record(prop);
      t[prop] = fn;
      return fn;
    },
    set(t, prop: string, value) {
      t[prop] = value;
      calls.push({ method: `set:${prop}`, args: [value] });
      return true;
    },
  });

  return {
    ctx: proxy as unknown as CanvasRenderingContext2D,
    calls,
    count: (method: string) => calls.filter((c) => c.method === method).length,
  };
}
