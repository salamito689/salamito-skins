# Teste gratuito de conectividade YouPin (Cloudflare Workers)

Este código é **somente diagnóstico**. Não envia cookies, login Steam, tokens, cabeçalhos falsificados nem faz requisições repetidas. Não grava anúncios nem publica ofertas.

## Implantação manual
1. Crie uma conta gratuita em https://dash.cloudflare.com/ (sem inserir dados de pagamento se não for necessário).
2. Entre em **Workers & Pages → Create → Worker** e crie um Worker.
3. No editor de código do Worker, substitua o conteúdo por `worker.js` desta pasta e clique em **Deploy**.
4. Acesse `https://SEU-WORKER.workers.dev/diagnostico` **uma vez** e compartilhe somente o JSON de resultado (não envie dados da conta).
5. Se retornar HTTP 403, 401 ou outro bloqueio, **pare o teste**. Não altere cabeçalhos, IPs ou credenciais para contornar restrições.

A consulta usa o endpoint público observado no navegador pelo usuário, mas isso **não equivale a autorização** para automatizar consultas. Para produção, é preciso verificar os termos de uso e obter acesso permitido. Não configure cron antes dessa validação.

O Worker retorna apenas código HTTP, contagem e nomes de campos, não dados de anúncios.
