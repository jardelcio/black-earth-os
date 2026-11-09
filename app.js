let STATE = {
  products: [],
  organizations: [],
  competitors: [],
  news_alerts: [],
  events: [],
  soil_problems: [],
  playbooks: [],
  schedules: [],
  runs: [],
  parameters: [],
  breakeven_soja: null,
  default_landed: null,
};

function showToast(msg) {
  const el = document.getElementById('app-toast');
  if (!el) return;
  el.textContent = msg;
  el.style.display = 'block';
  setTimeout(() => {
    el.style.display = 'none';
  }, 3600);
}

function fmtBRL(n) {
  return Number(n || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function fetchOverview() {
  const res = await fetch('/api/overview');
  STATE = await res.json();
  renderAll();
}

function renderAll() {
  renderSchedules();
  renderRadarAlerts();
  renderAutomationRuns();
  renderAccounts();
  renderBreakeven(STATE.breakeven_soja);
  renderSoilProblems();
  renderLanded(STATE.default_landed);
  renderCompetitors();
  renderEvents();
  renderPlaybooks();

  const accBadge = document.getElementById('badge-accounts');
  if (accBadge) accBadge.textContent = String(STATE.organizations.length);
  const kpiAcc = document.getElementById('kpi-total-accounts');
  if (kpiAcc) kpiAcc.textContent = `${STATE.organizations.length} Clusters`;
}

function renderSchedules() {
  const tbody = document.getElementById('schedules-tbody');
  if (!tbody) return;
  tbody.innerHTML = STATE.schedules.map((s) => `
    <tr>
      <td><strong class="mono-num">${s.job_code}</strong><div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">${s.job_name}</div></td>
      <td>${s.agent_owner}</td>
      <td><span class="badge badge-amber">${s.frequency_label}</span><div class="mono-num" style="font-size:11px; color:var(--text-muted); margin-top:4px;">cron: ${s.cron_expression}</div></td>
      <td style="max-width:340px; color:var(--text-secondary);">${s.description}</td>
      <td class="mono-num" style="font-size:12px;">${s.last_run_at || '—'}</td>
      <td><span class="badge badge-green">${s.last_status} (${s.items_processed} itens)</span></td>
      <td>
        <button class="btn" onclick="triggerJob('${s.job_code}')">Rodar Agora</button>
      </td>
    </tr>
  `).join('');
}

function renderRadarAlerts() {
  const box = document.getElementById('radar-alerts-container');
  if (!box) return;
  box.innerHTML = STATE.news_alerts.map((a) => `
    <div class="item-card">
      <div class="item-card-header">
        <div>
          <span class="badge badge-${a.impact_level}" style="margin-bottom:6px;">${a.impact_level} • ${a.category}</span>
          <div class="item-card-title">${a.title}</div>
        </div>
        <span class="mono-num" style="font-size:11px; color:var(--text-muted);">${a.published_at}</span>
      </div>
      <p style="color:var(--text-secondary); font-size:13px; margin-bottom:8px;">${a.summary}</p>
      <div style="font-size:12.5px; color:var(--accent-amber);">
        <strong>Ação (${a.affected_agent}):</strong> ${a.recommended_action}
      </div>
    </div>
  `).join('');
}

function renderAutomationRuns() {
  const box = document.getElementById('automation-runs-container');
  if (!box) return;
  box.innerHTML = STATE.runs.slice(0, 6).map((r) => `
    <div class="item-card">
      <div class="item-card-header">
        <div class="item-card-title mono-num">${r.job_code}</div>
        <span class="badge badge-green">${r.status.toUpperCase()}</span>
      </div>
      <div style="font-size:12px; color:var(--text-muted); margin-bottom:6px;">Agente: <strong>${r.agent_name}</strong> • Concluído: ${r.completed_at}</div>
      <p style="font-size:13px; color:var(--text-secondary);">${r.summary}</p>
    </div>
  `).join('');
}

function renderAccounts() {
  const tbody = document.getElementById('accounts-tbody');
  if (!tbody) return;
  const chFilter = document.getElementById('filter-channel')?.value || 'ALL';
  const ufFilter = document.getElementById('filter-uf')?.value || 'ALL';

  const filtered = STATE.organizations.filter((o) => {
    const passCh = chFilter === 'ALL' || o.channel_type === chFilter;
    const passUf = ufFilter === 'ALL' || o.uf === ufFilter;
    return passCh && passUf;
  });

  tbody.innerHTML = filtered.map((o) => {
    const badgeClass = o.total_score >= 90 ? 'badge-green' : 'badge-amber';
    return `
      <tr>
        <td>
          <span class="badge ${badgeClass}" style="font-size:13px;">${o.total_score}/100</span>
          <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">
            Fit:${o.fit_score} Vol:${o.volume_score} Acc:${o.access_score}
          </div>
        </td>
        <td>
          <strong>${o.name}</strong>
          <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">Culturas: ${o.crops}</div>
          <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">Fonte: ${o.provenance_status}</div>
        </td>
        <td>
          <span class="badge badge-neutral">${o.channel_type}</span>
          <div class="mono-num" style="margin-top:4px; font-size:12px;">UF: <strong>${o.uf}</strong> (${o.priority_uf})</div>
        </td>
        <td style="color:var(--accent-amber); font-weight:500;">${o.entry_door_role}</td>
        <td>
          <strong>${o.key_leader_name || '—'}</strong>
          <div style="font-size:12px; color:var(--text-secondary);">${o.key_leader_role || ''}</div>
        </td>
        <td><strong class="mono-num">${o.recommended_skus}</strong></td>
        <td>
          <select onchange="updateAccountStage(${o.id}, this.value)" style="background:var(--bg-base); color:var(--text-primary); border:1px solid var(--border-strong); padding:5px 8px; border-radius:4px; font-size:12px;">
            ${[
              'Empresa Mapeada',
              'Empresa Qualificada',
              'Decisor Identificado',
              'Abordagem Autorizada',
              'Contato Realizado',
              'Reunião Agendada',
              'Protocolo DBC / Trial',
              'Proposta Comercial'
            ].map((st) => `<option value="${st}" ${o.pipeline_stage === st ? 'selected' : ''}>${st}</option>`).join('')}
          </select>
        </td>
        <td style="max-width:280px; font-size:12.5px; color:var(--text-secondary);">${o.next_action}</td>
      </tr>
    `;
  }).join('');
}

function renderBreakeven(data) {
  if (!data) return;
  const tbody = document.getElementById('breakeven-tbody');
  if (tbody) {
    tbody.innerHTML = data.matrix.map((r) => `
      <tr>
        <td><strong>${r.sku}</strong> <span class="badge badge-neutral">${r.priority_tier}</span></td>
        <td>${r.family} • ${r.form}</td>
        <td class="mono-num">${r.dose_per_ha} ${r.unit}</td>
        <td class="mono-num">R$ ${fmtBRL(r.unit_price_brl)}</td>
        <td class="mono-num">R$ ${fmtBRL(r.freight_per_ha_brl)}</td>
        <td class="mono-num"><strong>R$ ${fmtBRL(r.cost_ha_brl)}</strong></td>
        <td class="mono-num">${r.breakeven_kg_ha.toFixed(1)} kg/ha</td>
        <td class="mono-num"><strong>${r.breakeven_sc_ha.toFixed(2)} sc/ha</strong></td>
        <td class="mono-num"><strong>${r.roi.toFixed(2)}x</strong></td>
        <td><span class="badge badge-${r.semaphore}">${r.semaphore}</span></td>
        <td style="font-size:12.5px; color:var(--text-secondary);">${r.commercial_rule}</td>
      </tr>
    `).join('');
  }

  const subBox = document.getElementById('map-substitution-box');
  if (subBox && data.map_substitution) {
    const m = data.map_substitution;
    subBox.innerHTML = `
      <div class="item-card">
        <div class="item-card-header">
          <div class="item-card-title">Redução de ${m.reduction_pct}% do MAP (${m.map_saved_kg_ha} kg/ha economizados)</div>
          <span class="badge ${m.approved ? 'badge-green' : 'badge-red'}">ROI Substituição: ${m.substitution_roi.toFixed(2)}x</span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:13px; margin-top:10px;">
          <div>Custo Base MAP (200 kg/ha): <strong class="mono-num">R$ ${fmtBRL(m.map_base_kg_ha * m.map_price_brl_kg)}/ha</strong></div>
          <div>Economia Direta de MAP (20%): <strong class="mono-num" style="color:var(--accent-emerald);">R$ ${fmtBRL(m.savings_brl_ha)}/ha</strong></div>
          <div>Custo GG16 (60 kg/ha + frete): <strong class="mono-num">R$ ${fmtBRL(m.gg16_cost_brl_ha)}/ha</strong></div>
          <div>Desembolso Adicional Líquido: <strong class="mono-num">R$ ${fmtBRL(m.net_additional_cost_brl_ha)}/ha</strong></div>
          <div>Receita Esperada Ganho: <strong class="mono-num">R$ ${fmtBRL(m.expected_gain_revenue_brl_ha)}/ha</strong></div>
          <div>Resultado Líquido Produtor: <strong class="mono-num" style="color:var(--accent-emerald);">+R$ ${fmtBRL(m.net_result_brl_ha)}/ha</strong></div>
        </div>
      </div>
    `;
  }
}

function renderSoilProblems() {
  const box = document.getElementById('soil-problems-container');
  if (!box) return;
  box.innerHTML = STATE.soil_problems.map((p) => `
    <div class="item-card">
      <div class="item-card-header">
        <div class="item-card-title">${p.problem_name}</div>
        <span class="badge badge-red">Perda: R$ ${fmtBRL(p.estimated_loss_brl_ha)}/ha</span>
      </div>
      <div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">Base: ${p.calculation_basis}</div>
      <div style="font-size:13px; color:var(--text-secondary); margin-bottom:6px;"><strong>Mecanismo Black Earth:</strong> ${p.black_earth_mechanism}</div>
      <div style="font-size:12.5px; color:var(--accent-amber);"><strong>Posicionamento:</strong> ${p.recommended_sku}</div>
    </div>
  `).join('');
}

function renderLanded(sim) {
  const box = document.getElementById('landed-results-container');
  if (!box || !sim) return;
  box.innerHTML = `
    <div class="two-col">
      <div class="item-card">
        <div class="item-card-header">
          <div class="item-card-title">Waterfall de Custo &amp; Margem — ${sim.sku} (${sim.channel_route})</div>
          <span class="badge badge-green">Margem BE: ${sim.black_earth_contribution_pct}%</span>
        </div>
        <table>
          <tbody>
            <tr><td>Custo FOB (${sim.fob_usd} US$ × R$ ${sim.exchange_rate})</td><td class="mono-num">R$ ${fmtBRL(sim.fob_brl)} / unid</td></tr>
            <tr><td>Logística Internacional &amp; Seguro</td><td class="mono-num">+ R$ ${fmtBRL(sim.international_logistics_brl)}</td></tr>
            <tr><td>Tributos Não-Recuperáveis (Hipótese Simulada)</td><td class="mono-num">+ R$ ${fmtBRL(sim.estimated_non_recoverable_taxes_brl)}</td></tr>
            <tr><td>Custo Financeiro &amp; Armazenagem</td><td class="mono-num">+ R$ ${fmtBRL(sim.financial_and_storage_brl)}</td></tr>
            <tr><td><strong>= Custo Econômico Entregue (Landed Cost)</strong></td><td class="mono-num"><strong>R$ ${fmtBRL(sim.landed_cost_brl)} / unid</strong></td></tr>
            <tr><td>Preço Líquido de Venda no Canal (Desc. Volume: ${sim.volume_discount_pct}%)</td><td class="mono-num"><strong>R$ ${fmtBRL(sim.net_selling_price_brl)} / unid</strong></td></tr>
            <tr><td>(-) Margem / Rebate do Canal</td><td class="mono-num">- R$ ${fmtBRL(sim.channel_margin_or_rebate_brl)}</td></tr>
            <tr><td>(-) Comissão Parceiro Técnico + Fundo de Ensaios</td><td class="mono-num">- R$ ${fmtBRL(sim.partner_commission_brl + sim.technical_trial_fund_brl)}</td></tr>
            <tr><td><strong>= Margem de Contribuição Líquida Black Earth</strong></td><td class="mono-num" style="color:var(--accent-emerald);"><strong>R$ ${fmtBRL(sim.black_earth_contribution_brl)} / unid (${sim.black_earth_contribution_pct}%)</strong></td></tr>
          </tbody>
        </table>
      </div>

      <div class="item-card">
        <div class="item-card-header">
          <div class="item-card-title">Argumento Econômico Oculto: 11% de Cinza vs 60% de Cinza</div>
          <span class="badge badge-amber">Lote: ${sim.volume_tons} toneladas</span>
        </div>
        <p style="font-size:13px; color:var(--text-secondary); margin-bottom:14px;">
          Com apenas <strong>11% de cinza</strong> contra 36–85% da leonardita comum, o comprador industrial transporta de 3 a 5 vezes menos terra inerte por quilo de ácido húmico ISO 19822.
        </p>
        <div style="display:grid; gap:10px; margin-bottom:14px;">
          <div style="background:var(--bg-base); padding:12px; border-radius:6px; border:1px solid var(--border-subtle);">
            <div style="font-size:12px; color:var(--text-secondary);">Custo por kg de Substância Húmica Ativa (Black Earth 11% Cinza)</div>
            <div class="mono-num" style="font-size:20px; font-weight:700; color:var(--accent-emerald);">R$ ${fmtBRL(sim.ash_advantage.cost_per_kg_active_hs_black_earth_brl)} / kg AH efetivo</div>
          </div>
          <div style="background:var(--bg-base); padding:12px; border-radius:6px; border:1px solid var(--border-subtle);">
            <div style="font-size:12px; color:var(--text-secondary);">Custo Equivalente Leonardita Genérica (60% Cinza Inerte)</div>
            <div class="mono-num" style="font-size:20px; font-weight:700; color:var(--accent-crimson);">R$ ${fmtBRL(sim.ash_advantage.cost_per_kg_active_hs_generic_brl)} / kg AH efetivo</div>
          </div>
        </div>
        <div style="font-size:13px; margin-bottom:10px;">
          Receita Total do Contrato (${sim.volume_tons}t): <strong class="mono-num">R$ ${fmtBRL(sim.total_contract_revenue_brl)}</strong><br/>
          Contribuição Total Black Earth: <strong class="mono-num" style="color:var(--accent-emerald);">R$ ${fmtBRL(sim.total_contract_contribution_brl)}</strong>
        </div>
        <div style="font-size:11.5px; color:var(--accent-amber); border-top:1px solid var(--border-subtle); padding-top:8px;">
          ${sim.governance_warning}
        </div>
      </div>
    </div>
  `;
}

function renderCompetitors() {
  const tbody = document.getElementById('competitors-tbody');
  if (!tbody) return;
  tbody.innerHTML = STATE.competitors.map((c) => `
    <tr>
      <td><strong>${c.company_product}</strong><div style="font-size:11.5px; color:var(--text-muted); margin-top:3px;">Cinza est.: ${c.ash_estimate}</div></td>
      <td>${c.origin_tech}</td>
      <td>${c.formulation}<div class="mono-num" style="margin-top:3px; font-size:12px; color:var(--accent-amber);">Dose: ${c.public_dose}</div></td>
      <td class="mono-num">${c.public_price_brl}</td>
      <td><span class="badge badge-green">${c.black_earth_counter_sku}</span></td>
      <td style="max-width:360px;">
        <div style="font-size:12.5px; color:var(--text-secondary); margin-bottom:4px;">${c.competitive_reading}</div>
        <div style="font-size:12.5px; color:var(--text-primary);"><strong>Defesa:</strong> ${c.defense_argument}</div>
      </td>
    </tr>
  `).join('');
}

function renderEvents() {
  const tbody = document.getElementById('events-tbody');
  if (!tbody) return;
  tbody.innerHTML = STATE.events.map((e) => `
    <tr>
      <td><strong>${e.event_name}</strong></td>
      <td class="mono-num">${e.location} • ${e.event_date}</td>
      <td><span class="badge badge-amber">${e.priority_level}</span></td>
      <td style="color:var(--accent-crimson); font-weight:600; font-size:12.5px;">${e.deadline_alert}</td>
      <td style="font-size:12.5px; color:var(--text-secondary);">${e.strategic_goal}</td>
      <td class="mono-num">${e.target_skus}</td>
    </tr>
  `).join('');
}

function renderPlaybooks() {
  const box = document.getElementById('playbooks-container');
  if (!box) return;
  box.innerHTML = STATE.playbooks.map((p) => {
    const isApproved = p.human_approval_status.startsWith('Aprovado');
    return `
      <div class="item-card">
        <div class="item-card-header">
          <div>
            <span class="badge badge-amber" style="margin-bottom:6px;">${p.cadence_step} • SKUs: ${p.sku_focus}</span>
            <div class="item-card-title">${p.title}</div>
            <div style="font-size:12.5px; color:var(--text-secondary); margin-top:2px;">
              <strong>Canal:</strong> ${p.target_channel} | <strong>Porta de Entrada:</strong> ${p.target_interlocutor}
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="badge ${isApproved ? 'badge-green' : 'badge-neutral'}">${p.human_approval_status}</span>
            <button class="btn ${isApproved ? '' : 'btn-emerald'}" onclick="approvePlaybook(${p.id}, '${isApproved ? 'Pendente Aprovação (AgroRemoto)' : 'Aprovado para Disparo (AgroRemoto)'}')">
              ${isApproved ? 'Reverter Status' : 'Aprovar Abordagem (Humano)'}
            </button>
          </div>
        </div>
        <div style="font-size:12.5px; margin-top:8px;"><strong>Assunto:</strong> ${p.subject_line}</div>
        <div class="pre-box">${p.message_body}</div>
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; font-size:12px; color:var(--text-secondary);">
          <div><strong>Anexos Obrigatórios:</strong> ${p.required_attachments}</div>
          <div><strong>Gate Regulatório:</strong> <span class="mono-num" style="color:var(--accent-amber);">${p.compliance_gate_status}</span></div>
        </div>
      </div>
    `;
  }).join('');
}

async function triggerJob(jobCode) {
  showToast(`Executando automação ${jobCode}...`);
  await fetch('/api/automations/trigger', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_code: jobCode }),
  });
  await fetchOverview();
  showToast(`Automação ${jobCode} concluída e relatórios atualizados!`);
}

async function approvePlaybook(id, status) {
  await fetch('/api/playbooks/approve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, status }),
  });
  await fetchOverview();
  showToast(`Status do playbook atualizado: ${status}`);
}

async function updateAccountStage(id, stage) {
  await fetch('/api/accounts/stage', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, stage }),
  });
  showToast(`Estágio da conta atualizado para: ${stage}`);
}

document.addEventListener('DOMContentLoaded', () => {
  // Navigation tabs
  document.querySelectorAll('.nav-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-btn').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add('active');
    });
  });

  // Trigger all agents button
  document.getElementById('btn-run-all-agents')?.addEventListener('click', () => {
    triggerJob('ALL');
  });

  // Account filters
  document.getElementById('filter-channel')?.addEventListener('change', renderAccounts);
  document.getElementById('filter-uf')?.addEventListener('change', renderAccounts);

  // Add account
  document.getElementById('btn-add-account')?.addEventListener('click', async () => {
    const name = document.getElementById('new-acc-name')?.value.trim();
    if (!name) {
      showToast('Informe o nome da organização.');
      return;
    }
    const channel_type = document.getElementById('new-acc-channel')?.value;
    const uf = document.getElementById('new-acc-uf')?.value.trim() || 'MT';
    const key_leader_name = document.getElementById('new-acc-leader')?.value.trim() || 'Coordenador Técnico';
    const recommended_skus = document.getElementById('new-acc-skus')?.value.trim() || 'Fuze DS, Alpha, Magna';

    await fetch('/api/accounts/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, channel_type, uf, key_leader_name, recommended_skus }),
    });
    document.getElementById('new-acc-name').value = '';
    await fetchOverview();
    showToast(`Conta "${name}" qualificada e adicionada ao CRM!`);
  });

  // Break-even crop selector sync
  const defaultPrices = {
    P_SOJA: 2.083,
    P_CAFE: 23.33,
    P_ALG: 9.67,
    P_MILHO: 1.133,
    P_BATATA: 2.20,
    P_TRIGO: 1.25,
    P_CANA: 0.145,
  };
  document.getElementById('be-crop-select')?.addEventListener('change', async (e) => {
    const code = e.target.value;
    const priceInput = document.getElementById('be-crop-price');
    if (priceInput && defaultPrices[code]) {
      priceInput.value = defaultPrices[code];
    }
    document.getElementById('btn-calc-breakeven')?.click();
  });

  document.getElementById('btn-calc-breakeven')?.addEventListener('click', async () => {
    const code = document.getElementById('be-crop-select')?.value || 'P_SOJA';
    const price = document.getElementById('be-crop-price')?.value || '2.083';
    const hc = document.getElementById('be-haircut')?.value || '0.60';
    const res = await fetch(`/api/simulators/breakeven?crop_code=${encodeURIComponent(code)}&crop_price=${encodeURIComponent(price)}&haircut=${encodeURIComponent(hc)}`);
    const data = await res.json();
    renderBreakeven(data);
    showToast(`Matriz Break-Even recalculada para ${data.crop_name}!`);
  });

  // Landed simulator button
  document.getElementById('btn-calc-landed')?.addEventListener('click', async () => {
    const sku = document.getElementById('sim-sku')?.value || 'Fuze DS';
    const route = document.getElementById('sim-route')?.value || 'OEM / Indústria Importadora';
    const fob = document.getElementById('sim-fob')?.value || '7.20';
    const fx = document.getElementById('sim-fx')?.value || '5.45';
    const tax = document.getElementById('sim-tax')?.value || '18.5';
    const comm = document.getElementById('sim-comm')?.value || '5.0';
    const margin = document.getElementById('sim-margin')?.value || '22.0';
    const vol = document.getElementById('sim-vol')?.value || '20';

    const url = `/api/simulators/landed?sku=${encodeURIComponent(sku)}&route=${encodeURIComponent(route)}&fob_usd=${fob}&exchange_rate=${fx}&tax_pct=${tax}&commission_pct=${comm}&channel_margin_pct=${margin}&volume_tons=${vol}`;
    const res = await fetch(url);
    const data = await res.json();
    renderLanded(data);
    showToast(`Simulação Landed-to-Channel atualizada para ${sku}!`);
  });

  fetchOverview();
});
