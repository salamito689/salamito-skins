#!/usr/bin/env node
// Salamito Skins: reconciliacao de anuncios individuais. Node >=18.
// Entrada: JSON autorizado de uma fonte com inventario COMPLETO; nunca um recorte de pagina.
// Nao consulta nem contorna a API da YouPin. Nao publica inventario parcial.
const fs = require('node:fs');
const crypto = require('node:crypto');
const input = process.argv[2];
const previousPath = process.argv[3];
const output = process.argv[4];
if (!input || !previousPath || !output) {
  console.error('Uso: node scripts/reconcile-youpin.cjs entrada.json anterior.json saida.json');
  process.exit(2);
}
function read(path) { return JSON.parse(fs.readFileSync(path, 'utf8')); }
function fail(message) { throw Error(message); }
function listing(x) {
  if (!x || typeof x !== 'object') fail('Anuncio invalido');
  const id = String(x.id ?? x.listing_id ?? '').trim();
  const name = String(x.market_hash_name ?? x.commodityHashName ?? '').trim();
  const cny = Number(x.price_cny ?? x.price);
  const float = Number(x.float ?? x.abrade);
  const seed = Number(x.paint_seed ?? x.paintSeed);
  const inspect = String(x.inspect_link ?? x.inspect ?? x.actions?.[0]?.link ?? '').trim();
  if (!/^\d+$/.test(id) || !name || !(cny > 0) || !Number.isFinite(float) || float < 0 || float > 1 ||
      !Number.isInteger(seed) || seed < 0 || seed > 1000 || !/^steam:\/\/rungame\/730\//.test(inspect)) {
    fail('Campos invalidos ou ausentes no anuncio ' + (id || '?') + ': id, nome, preco, float, seed, inspect');
  }
  return { id, market_hash_name: name, price_cny: cny, float, paint_seed: seed, inspect_link: inspect };
}
function run() {
  const source = read(input);
  if (source.complete_inventory !== true) fail('Fonte nao confirmou inventario completo: recusando reconciliacao');
  if (!source.captured_at || !Number.isFinite(Date.parse(source.captured_at))) fail('captured_at invalido');
  if (Date.parse(source.captured_at) > Date.now() + 300000) fail('Captura no futuro');
  if (Date.now() - Date.parse(source.captured_at) > 15 * 60000) fail('Captura antiga (>15 minutos)');
  if (!Array.isArray(source.listings)) fail('listings precisa ser array');
  const incoming = new Map();
  for (const raw of source.listings) {
    const item = listing(raw);
    if (incoming.has(item.id)) fail('ID duplicado: ' + item.id);
    incoming.set(item.id, item);
  }
  const old = fs.existsSync(previousPath) ? read(previousPath) : { listings: [] };
  const before = new Map((old.listings || []).map(x => [String(x.id), x]));
  const changes = { added: [], updated: [], removed: [] };
  for (const [id, item] of incoming) {
    if (!before.has(id)) changes.added.push(id);
    else if (JSON.stringify(before.get(id)) !== JSON.stringify(item)) changes.updated.push(id);
  }
  for (const id of before.keys()) if (!incoming.has(id)) changes.removed.push(id);
  const result = {
    schema_version: 1,
    source: source.source || 'authorized_feed',
    captured_at: source.captured_at,
    generated_at: new Date().toISOString(),
    complete_inventory: true,
    listings: [...incoming.values()].sort((a,b) => a.id.localeCompare(b.id)),
    changes
  };
  // Escrita atomica: um arquivo incompleto nao substitui inventario anterior.
  const temp = output + '.' + crypto.randomBytes(6).toString('hex') + '.tmp';
  fs.writeFileSync(temp, JSON.stringify(result, null, 2) + '\n');
  fs.renameSync(temp, output);
  console.log(JSON.stringify({ total: incoming.size, changes }));
}
try { run(); } catch (e) { console.error('SINCRONIZACAO RECUSADA:', e.message); process.exit(1); }
