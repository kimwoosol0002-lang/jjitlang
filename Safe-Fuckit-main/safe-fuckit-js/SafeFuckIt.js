'use strict';

class SafeFuckIt {
  constructor(options = {}) {
    this.exTypes = options.exTypes || [Error];
    this.targetGlobals = options.targetGlobals || null;
    this._snapshot = null;
  }

  _getEffectiveGlobals() {
    if (this.targetGlobals !== null) {
      return this.targetGlobals;
    }
    return {};
  }

  _takeSnapshot() {
    const target = this._getEffectiveGlobals();
    const snapshot = {};
    const ownKeys = Reflect.ownKeys(target).filter(k => typeof k === 'string');
    for (const key of ownKeys) {
      if (key.startsWith('__') || typeof target[key] === 'function') continue;
      try {
        snapshot[key] = structuredClone(target[key]);
      } catch {
        snapshot[key] = target[key];
      }
    }
    this._snapshot = snapshot;
  }

  _handleException(error) {
    console.error('[safe_fuckit] Exception isolated successfully!');
    console.error(`   - Reason  : ${error.constructor.name}: ${error.message}`);
    const stackLines = error.stack ? error.stack.split('\n') : [];
    if (stackLines.length > 1) {
      console.error(`   - Location: ${stackLines[1].trim()}`);
    }

    const target = this._getEffectiveGlobals();
    if (target && this._snapshot) {
      console.warn('[safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.');
      const ownKeys = Reflect.ownKeys(target).filter(k => typeof k === 'string');
      for (const key of ownKeys) {
        if (!key.startsWith('__') && !(key in this._snapshot) && typeof target[key] !== 'function') {
          delete target[key];
        }
      }
      for (const [key, value] of Object.entries(this._snapshot)) {
        target[key] = value;
      }
    }
  }

  wrap(fn) {
    const self = this;
    const isAsync = fn.constructor.name === 'AsyncFunction';

    if (isAsync) {
      return async function (...args) {
        self._takeSnapshot();
        try {
          return await fn.apply(this, args);
        } catch (err) {
          if (self.exTypes.some(et => err instanceof et)) {
            self._handleException(err);
            return;
          }
          throw err;
        }
      };
    }

    return function (...args) {
      self._takeSnapshot();
      try {
        return fn.apply(this, args);
      } catch (err) {
        if (self.exTypes.some(et => err instanceof et)) {
          self._handleException(err);
          return;
        }
        throw err;
      }
    };
  }

  enter() {
    this._takeSnapshot();
    return this;
  }

  exit() {
    this._snapshot = null;
  }
}

function safeFuckit(a, b) {
  if (typeof a === 'function') {
    return new SafeFuckIt(b || {}).wrap(a);
  }
  return new SafeFuckIt(a || {});
}

module.exports = { SafeFuckIt, safeFuckit };
