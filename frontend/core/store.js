/**
 * Store global lleuger — estat compartit entre mòduls.
 * Ús: Store.set('portfolio', data) / Store.get('portfolio')
 */
import Events from './events.js';

const Store = (() => {
  const state = {
    portfolio: null,
    lastUpdated: null,
    isLoading: false,
  };

  return {
    get(key) {
      return state[key];
    },

    set(key, value) {
      state[key] = value;
      Events.emit(`store:${key}`, value);
    },

    getAll() {
      return { ...state };
    },
  };
})();

window.Store = Store;
export default Store;
