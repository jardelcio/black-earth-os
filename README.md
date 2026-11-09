# Black Earth — Commercial Intelligence OS | AgroRemoto

Plataforma Web Dedicada e Motor Multiagente de Automação Comercial para a operação da **Black Earth** no Brasil e América do Sul.

## Módulos Inclusos

1. **Quadro Kanban Interativo de Avanço de Contatos (5 Etapas B2B):**
   - `1. Mapeado / Qualificado`
   - `2. Contato Técnico (Semana 1)`
   - `3. Reunião 40m & Teste Jarro (Semana 2)`
   - `4. Protocolo DBC / Piloto OEM`
   - `5. Proposta / Contrato & Barter`
   - Suporte a *Drag & Drop* (arrastar e soltar), botões rápidos `◀ / ▶`, registro de histórico de interações com data/hora e salvamento automático no navegador (`localStorage`).
2. **Tabela CRM Reverso & Lead Score (0–100):**
   - Qualificação multicritério (Fit 25, Volume 20, Acesso 15, Regulatório 15, Técnico 15, Operacional 10) e trava de porta de entrada técnica.
3. **Simulador Dinâmico de Break-Even, Substituição de 20% do MAP & Custo do Problema:**
   - Cálculos automáticos para Soja, Café Arábica, Algodão, Milho, Batata/HF, Trigo e Cana-de-Açúcar (ATR).
4. **Simulador Landed-to-Channel & Economia de 11% de Cinza:**
   - Comparativo de custo entregue e custo por kg de Ácido Húmico ativo (11% de cinza da Humalite Black Earth vs 60% de cinza da leonardita genérica).
5. **Matriz de Concorrência & Calendário de Feiras 2027:**
   - Monitoramento de 10 linhas concorrentes (HGS BioScience, Rigrantec, Healthy BioSolutions, Liphatech, Coda, Plantpar, Leonardita Australiana) e alerta de 60 dias para as vitrines de 2027.
6. **Playbooks B2B & Cadência de 5 Semanas (Gates R0–R4):**
   - Roteiros prontos por interlocutor com trava de aprovação humana (`human_approval_required`).
7. **Automação Agendada (Cron Diário às 07:00 BRT via GitHub Actions / Python):**
   - Workflow em `.github/workflows/deploy-and-cron.yml` que atualiza relatórios e publica o painel no GitHub Pages automaticamente.

## Como Publicar em 1 Minuto

### Opção 1 — GitHub Pages
1. Suba os arquivos deste repositório em um repositório no GitHub.
2. Vá em **Settings → Pages → Build and deployment → Source** e selecione **GitHub Actions**.
3. O workflow `.github/workflows/deploy-and-cron.yml` publicará automaticamente o painel web em `https://<seu-usuario>.github.io/<nome-do-repo>/` e executará a rotina diária às 07:00 BRT.

### Opção 2 — Vercel ou Netlify Drop
1. Acesse [app.netlify.com/drop](https://app.netlify.com/drop) ou [vercel.com/new](https://vercel.com/new).
2. Arraste a pasta do projeto (ou o arquivo `black-earth-os-deploy.zip`).
3. Sua URL `https://` dedicada estará no ar instantaneamente.
