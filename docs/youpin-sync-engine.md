# Motor de reconciliacao YouPin (fase preparatoria)

Este motor **nao esta conectado a YouPin**. O acesso automatizado a anuncios individuais ainda depende de uma fonte autorizada. O teste anterior de consulta direta em GitHub Actions retornou HTTP 403.

## Contrato de entrada
JSON com `complete_inventory: true`, `captured_at` ISO recente (ate 15 minutos), `source` e `listings` com `id`, `market_hash_name`, `price_cny`, `float`, `paint_seed` e `inspect_link` Steam. A fonte precisa assegurar que a consulta cobriu **todas as paginas** e **todo o universo de anuncios pretendido** antes de definir `complete_inventory: true`. Uma pagina parcial ou captura historica nao pode ser promovida a estoque atual.

## Executar localmente
```bash
node scripts/reconcile-youpin.cjs feed-completo.json estado-anterior.json novo-estado.json
```

O script valida dados, identifica IDs novos, alterados e removidos, e grava um estado novo atomicamente. Se a fonte estiver incompleta, desatualizada ou inconsistente, falha sem substituir o estado anterior. O site publico nao e alterado por este script.

## Pendencias para producao
1. Contratar ou receber acesso autorizado a feed de **anuncios ativos individuais** com IDs, floats, patterns e inspect.
2. Implementar paginacao completa e verificacao de cobertura, com limite de taxa da fonte.
3. Adicionar agendamento/worker e publicacao com validade curta e falha fechada: sem sincronizacao recente, nao anunciar disponibilidade.
4. Integrar `data/youpin-listings.json` e interface, mantendo `data/youpin-snapshot.json` historico.
5. Verificar latencia e disponibilidade: polling nao equivale a atualizacao instantanea.
