/**
 * Client HTTP centralitzat.
 * Tota crida a l'API passa per aquí — mai fetch() directe als mòduls.
 * Ús: API.get('/api/v1/portfolio/summary')
 *     API.post('/api/v1/sync/upload', formData)
 */
import Events from './events.js';

const API = (() => {
  const BASE = '';  // Nginx fa proxy de /api/ → backend

  async function request(method, path, body = null) {
    Events.emit('api:loading', true);

    const options = {
      method,
      headers: {},
    };

    if (body instanceof FormData) {
      options.body = body;
    } else if (body !== null) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }

    try {
      const res = await fetch(`${BASE}${path}`, options);
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const err = new Error(data.error || `HTTP ${res.status}`);
        err.status = res.status;
        throw err;
      }

      return data;
    } catch (err) {
      Events.emit('api:error', err);
      throw err;
    } finally {
      Events.emit('api:loading', false);
    }
  }

  return {
    get:    (path)         => request('GET',    path),
    post:   (path, body)   => request('POST',   path, body),
    put:    (path, body)   => request('PUT',    path, body),
    delete: (path)         => request('DELETE', path),
    patch:  (path, body)   => request('PATCH',  path, body),
  };
})();

window.API = API;
export default API;
