export class Attic {
  constructor({ url = 'http://localhost:4000', key = 'dev-key', namespace = 'default' } = {}) {
    this.url = url.replace(/\/$/, ''); this.key = key; this.namespace = namespace;
  }
  async call(path, options = {}) {
    const response = await fetch(this.url + path, { ...options, headers: { 'x-attic-key': this.key, 'content-type': 'application/json', ...(options.headers || {}) } });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  }
  remember(content, source, tags = [], namespace = this.namespace) { return this.call('/memory', { method: 'POST', body: JSON.stringify({ content, source, tags, namespace }) }); }
  recall(query, { limit = 5, tag, namespace = this.namespace } = {}) { const p = new URLSearchParams({ q: query, limit, namespace }); if (tag) p.set('tag', tag); return this.call('/recall?' + p); }
  ask(question, namespace = this.namespace) { return this.call('/ask?' + new URLSearchParams({ q: question, namespace })); }
  forget(id) { return this.call('/memory/' + encodeURIComponent(id), { method: 'DELETE' }); }
}
