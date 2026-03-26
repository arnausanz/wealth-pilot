/**
 * Event bus global — comunicació entre mòduls sense acoplament.
 * Ús: Events.on('portfolio:updated', handler) / Events.emit('portfolio:updated', data)
 */
const Events = (() => {
  const listeners = new Map();

  return {
    on(event, handler) {
      if (!listeners.has(event)) listeners.set(event, new Set());
      listeners.get(event).add(handler);
    },

    off(event, handler) {
      listeners.get(event)?.delete(handler);
    },

    emit(event, data) {
      listeners.get(event)?.forEach((handler) => handler(data));
    },

    once(event, handler) {
      const wrapper = (data) => { handler(data); this.off(event, wrapper); };
      this.on(event, wrapper);
    },
  };
})();

window.Events = Events;
export default Events;
