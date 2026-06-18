type AbstractConstructor<T> = abstract new (...args: unknown[]) => T;

export interface SafeFuckItOptions {
  exTypes?: Array<abstract new (...args: unknown[]) => Error>;
  targetGlobals?: Record<string, unknown> | null;
}

export class SafeFuckIt {
  private exTypes: Array<abstract new (...args: unknown[]) => Error>;
  private targetGlobals: Record<string, unknown> | null;
  private _snapshot: Record<string, unknown> | null = null;

  constructor(options: SafeFuckItOptions = {}) {
    this.exTypes = options.exTypes ?? [Error];
    this.targetGlobals = options.targetGlobals ?? null;
  }

  private _getEffectiveGlobals(): Record<string, unknown> {
    if (this.targetGlobals !== null) {
      return this.targetGlobals;
    }
    return {};
  }

  private _takeSnapshot(): void {
    const target = this._getEffectiveGlobals();
    const snapshot: Record<string, unknown> = {};
    for (const key of Object.getOwnPropertyNames(target)) {
      if (key.startsWith('__') || typeof target[key] === 'function') continue;
      try {
        snapshot[key] = structuredClone(target[key]);
      } catch {
        snapshot[key] = target[key];
      }
    }
    this._snapshot = snapshot;
  }

  private _handleException(error: Error): void {
    console.error('[safe_fuckit] Exception isolated successfully!');
    console.error(`   - Reason  : ${error.constructor.name}: ${error.message}`);
    const stackLines = error.stack ? error.stack.split('\n') : [];
    if (stackLines.length > 1) {
      console.error(`   - Location: ${stackLines[1].trim()}`);
    }

    const target = this._getEffectiveGlobals();
    if (target && this._snapshot) {
      console.warn('[safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.');
      for (const key of Object.getOwnPropertyNames(target)) {
        if (!key.startsWith('__') && !(key in this._snapshot!) && typeof target[key] !== 'function') {
          delete target[key];
        }
      }
      for (const [key, value] of Object.entries(this._snapshot)) {
        target[key] = value;
      }
    }
  }

  wrap<T extends (...args: unknown[]) => unknown>(fn: T): T {
    const self = this;
    const isAsync = fn.constructor.name === 'AsyncFunction';

    if (isAsync) {
      const wrapped = async function (this: unknown, ...args: unknown[]) {
        self._takeSnapshot();
        try {
          return await fn.apply(this, args);
        } catch (err) {
          if (self.exTypes.some(et => err instanceof et)) {
            self._handleException(err as Error);
            return;
          }
          throw err;
        }
      };
      return wrapped as unknown as T;
    }

    const wrapped = function (this: unknown, ...args: unknown[]) {
      self._takeSnapshot();
      try {
        return fn.apply(this, args);
      } catch (err) {
        if (self.exTypes.some(et => err instanceof et)) {
          self._handleException(err as Error);
          return;
        }
        throw err;
      }
    };
    return wrapped as unknown as T;
  }

  enter(): this {
    this._takeSnapshot();
    return this;
  }

  exit(): void {
    this._snapshot = null;
  }
}

export function safeFuckit<T extends (...args: unknown[]) => unknown>(fn: T, options?: SafeFuckItOptions): T;
export function safeFuckit(options?: SafeFuckItOptions): SafeFuckIt;
export function safeFuckit<T extends (...args: unknown[]) => unknown>(
  a?: T | SafeFuckItOptions,
  b?: SafeFuckItOptions,
): T | SafeFuckIt {
  if (typeof a === 'function') {
    return new SafeFuckIt(b || {}).wrap(a);
  }
  return new SafeFuckIt(a || {});
}
