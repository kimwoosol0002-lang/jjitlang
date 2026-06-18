// Safe-Fuckit TypeScript Implementation

export type ExceptionType = new (...args: any[]) => Error;

export interface SafeFuckItOptions {
  exTypes?: ExceptionType[];
  targetGlobals?: Record<string, any> | null;
}

export interface SafeFuckItAsyncOptions extends SafeFuckItOptions {
  timeout?: number;
}

/**
 * Result type for error capture operations
 */
export interface ErrorResult<T = unknown> {
  value: T | null;
  error: Error | null;
  success: boolean;
}

/**
 * SafeFuckIt class for isolating exceptions and rolling back state
 */
export class SafeFuckIt {
  private exTypes: ExceptionType[];
  private targetGlobals: Record<string, any> | null;
  private snapshot: Record<string, any> | null;

  /**
   * Initialize SafeFuckIt
   * @param options Configuration options
   */
  constructor(options?: SafeFuckItOptions) {
    this.exTypes = options?.exTypes || [Error];
    this.targetGlobals = options?.targetGlobals || null;
    this.snapshot = null;
  }

  /**
   * Get effective globals object
   */
  private getEffectiveGlobals(): Record<string, any> {
    if (this.targetGlobals !== null) {
      return this.targetGlobals;
    }
    return {};
  }

  /**
   * Take a snapshot of current state
   */
  private takeSnapshot(): void {
    const target = this.getEffectiveGlobals();
    const snapshot: Record<string, any> = {};
    const ownKeys = Reflect.ownKeys(target).filter((k) => typeof k === 'string');

    for (const key of ownKeys) {
      const strKey = key as string;
      if (strKey.startsWith('__') || typeof target[strKey] === 'function') {
        continue;
      }
      try {
        snapshot[strKey] = structuredClone(target[strKey]);
      } catch {
        snapshot[strKey] = target[strKey];
      }
    }
    this.snapshot = snapshot;
  }

  /**
   * Handle exception
   */
  private handleException(error: Error): void {
    console.error('[safe_fuckit] Exception isolated successfully!');
    console.error(`   - Reason  : ${error.constructor.name}: ${error.message}`);
    const stackLines = error.stack ? error.stack.split('\n') : [];
    if (stackLines.length > 1) {
      console.error(`   - Location: ${stackLines[1].trim()}`);
    }

    const target = this.getEffectiveGlobals();
    if (target && this.snapshot) {
      console.warn(
        '[safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.'
      );
      const ownKeys = Reflect.ownKeys(target).filter((k) => typeof k === 'string');
      for (const key of ownKeys) {
        const strKey = key as string;
        if (
          !strKey.startsWith('__') &&
          !(strKey in this.snapshot) &&
          typeof target[strKey] !== 'function'
        ) {
          delete target[strKey];
        }
      }
      for (const [key, value] of Object.entries(this.snapshot)) {
        target[key] = value;
      }
    }
  }

  /**
   * Wrap a function with exception isolation
   * @param fn Function to wrap
   * @returns Wrapped function
   */
  wrap<T extends (...args: any[]) => any>(fn: T): T {
    const self = this;
    const isAsync = fn.constructor.name === 'AsyncFunction';

    if (isAsync) {
      return (async function (this: any, ...args: any[]) {
        self.takeSnapshot();
        try {
          return await fn.apply(this, args);
        } catch (err) {
          if (self.exTypes.some((et) => err instanceof et)) {
            self.handleException(err as Error);
            return;
          }
          throw err;
        }
      } as any) as T;
    }

    return (function (this: any, ...args: any[]) {
      self.takeSnapshot();
      try {
        return fn.apply(this, args);
      } catch (err) {
        if (self.exTypes.some((et) => err instanceof et)) {
          self.handleException(err as Error);
          return;
        }
        throw err;
      }
    } as any) as T;
  }

  /**
   * Enter snapshot mode
   * @returns this
   */
  enter(): this {
    this.takeSnapshot();
    return this;
  }

  /**
   * Exit snapshot mode
   */
  exit(): void {
    this.snapshot = null;
  }
}

/**
 * Wrap a function with exception isolation
 * @param fn Function to wrap
 * @param options Configuration options
 * @returns Wrapped function
 */
export function safeFuckit<T extends (...args: any[]) => any>(
  fn: T,
  options?: SafeFuckItOptions
): T;

/**
 * Create SafeFuckIt instance
 * @param options Configuration options
 * @returns SafeFuckIt instance
 */
export function safeFuckit(options?: SafeFuckItOptions): SafeFuckIt;

export function safeFuckit<T extends (...args: any[]) => any>(
  a?: T | SafeFuckItOptions,
  b?: SafeFuckItOptions
): T | SafeFuckIt {
  if (typeof a === 'function') {
    return new SafeFuckIt(b || {}).wrap(a) as T;
  }
  return new SafeFuckIt(a || {});
}

export default safeFuckit;
