// Corneteiro frontend — vanilla JS SPA consumindo a API Flask local
(() => {
  const API_BASE = ""; // mesma origem

  // -------------------- utils --------------------
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => [...root.querySelectorAll(sel)];

  const fmtMoeda = (v) =>
    v == null
      ? "—"
      : Number(v)
          .toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })
          .replace("R$", "C$");

  const fmtNum = (v, digits = 2) =>
    v == null || Number.isNaN(Number(v))
      ? "—"
      : Number(v).toLocaleString("pt-BR", {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        });

  const fmtPct = (v, digits = 1) =>
    v == null || Number.isNaN(Number(v))
      ? "—"
      : (Number(v) * 100).toLocaleString("pt-BR", {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        }) + "%";

  const escapeHtml = (s) =>
    String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const normalize = (s) =>
    String(s ?? "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();

  async function api(path, params = {}) {
    const url = new URL(API_BASE + path, window.location.origin);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, v);
      }
    });
    const res = await fetch(url.toString(), {
      headers: { Accept: "application/json" },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.mensagem || data?.detalhe || data?.erro || `Erro ${res.status}`;
      throw new Error(msg);
    }
    return data;
  }

  function showError(container, err) {
    container.innerHTML = `
      <div class="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4 text-sm">
        <div class="font-semibold mb-1">Falha ao consultar API</div>
        <div>${escapeHtml(err.message || err)}</div>
      </div>
    `;
  }

  function loadingBox(label = "carregando…") {
    return `
      <div class="p-8 text-center text-sm text-ink-400">
        <span class="spinner"></span> ${escapeHtml(label)}
      </div>
    `;
  }

  // -------------------- roteamento (hash) --------------------
  const ROUTES = ["#/recomendacoes", "#/atletas", "#/clubes"];

  function setRoute(hash) {
    if (!ROUTES.includes(hash)) hash = "#/recomendacoes";
    window.location.hash = hash;
  }

  function onRouteChange() {
    let hash = window.location.hash;
    if (!ROUTES.includes(hash)) hash = "#/recomendacoes";
    const view = hash.replace("#/", "");

    qsa("[data-view]").forEach((el) => {
      el.classList.toggle("is-active", el.dataset.view === view);
    });
    qsa("#nav-tabs .tab-btn").forEach((btn) => {
      btn.setAttribute(
        "aria-selected",
        btn.dataset.route === hash ? "true" : "false"
      );
    });

    if (view === "clubes" && !state.clubesCarregados) carregarClubes();
  }

  // -------------------- estado --------------------
  const state = {
    rodadaAtual: null,
    clubesPorId: {},
    clubesCarregados: false,
    clubesLista: [],
    clubeFiltro: "",
  };

  // -------------------- mercado / status --------------------
  async function carregarStatusMercado() {
    const box = qs("#market-status");
    box.classList.remove("hidden");
    box.innerHTML = `<span class="spinner"></span><span>mercado…</span>`;
    try {
      const data = await api("/mercado/status");
      const rodada =
        data?.rodada_atual ?? data?.mercado?.rodada_atual ?? data?.rodada;
      const aberto =
        data?.status_mercado === 1 ||
        data?.mercado?.status_mercado === 1 ||
        data?.aberto === true;
      state.rodadaAtual = rodada;
      const dot = aberto ? "bg-green-500" : "bg-red-500";
      const texto = aberto ? "Mercado aberto" : "Mercado fechado";
      box.innerHTML = `
        <span class="w-2 h-2 rounded-full ${dot}"></span>
        <span>${texto}${rodada ? ` · Rodada ${rodada}` : ""}</span>
      `;
      const chip = qs("#reco-rodada-chip");
      if (rodada) {
        chip.style.display = "inline-flex";
        chip.textContent = `Rodada ${rodada}`;
      }
    } catch (err) {
      box.innerHTML = `<span class="chip chip-red">mercado indisponível</span>`;
    }
  }

  // -------------------- Recomendações --------------------
  const RECO_CRITERIOS = {
    custo_beneficio: {
      titulo: "Custo-benefício",
      descricao:
        "Encontra atletas com a melhor relação entre pontuação média e preço. Ideal para montar um time competitivo sem gastar muitas cartoletas.",
    },
    destaques_rodada: {
      titulo: "Destaques da rodada",
      descricao:
        "Lista os atletas que mais pontuaram em uma rodada específica. Bom para identificar quem está em boa fase e repetir escalações vencedoras.",
    },
    misto: {
      titulo: "Misto",
      descricao:
        "Combina forma recente, consistência e custo-benefício num único score. Equilibra desempenho com regularidade — boa escolha para quem busca atletas confiáveis a longo prazo.",
    },
    confronto_hibrido: {
      titulo: "Confronto híbrido",
      descricao:
        "Leva em conta o desempenho individual do atleta e o quão vulnerável é o adversário da próxima rodada. Ideal para explorar confrontos favoráveis e maximizar pontos na rodada.",
    },
    valorizacao: {
      titulo: "Valorização",
      descricao:
        "Seleciona atletas com alta probabilidade de valorizar no mercado após a rodada. Perfeito para quem quer aumentar o patrimônio da equipe comprando antes da alta.",
    },
  };

  let criterioAtual = "custo_beneficio";

  function atualizarFiltrosCriterio() {
    qsa("#reco-form [data-show-for]").forEach((el) => {
      el.style.display = el.dataset.showFor === criterioAtual ? "flex" : "none";
    });
  }

  function atualizarDescricaoCriterio() {
    const el = qs("#reco-criterio-descricao");
    if (el) el.textContent = RECO_CRITERIOS[criterioAtual]?.descricao ?? "";
  }

  function setupRecoTabs() {
    qsa("#reco-criterio-tabs .tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        criterioAtual = btn.dataset.criterio;
        qsa("#reco-criterio-tabs .tab-btn").forEach((b) =>
          b.setAttribute(
            "aria-selected",
            b.dataset.criterio === criterioAtual ? "true" : "false"
          )
        );
        atualizarFiltrosCriterio();
        atualizarDescricaoCriterio();
      });
    });
    atualizarFiltrosCriterio();
    atualizarDescricaoCriterio();
  }

  function paramsDoForm() {
    const form = qs("#reco-form");
    const fd = new FormData(form);
    const params = { criterio: criterioAtual };
    for (const [k, v] of fd.entries()) {
      if (v !== "" && v !== null) {
        const campo = form.querySelector(`[name="${k}"]`);
        const wrapper = campo?.closest("[data-show-for]");
        if (wrapper && wrapper.dataset.showFor !== criterioAtual) continue;
        params[k] = v;
      }
    }
    return params;
  }

  function cellCriterio(item, criterio) {
    switch (criterio) {
      case "custo_beneficio":
        return [
          { label: "Preço", value: fmtMoeda(item.preco_num) },
          { label: "Média", value: fmtNum(item.media_num) },
          {
            label: "Índice",
            value: fmtNum(item.indice_custo_beneficio),
            accent: true,
          },
        ];
      case "destaques_rodada":
        return [
          { label: "Preço", value: fmtMoeda(item.preco_num) },
          { label: "Pts Cartola", value: fmtNum(item.pontuacao_cartola) },
          {
            label: "Pts Calc.",
            value: fmtNum(item.pontuacao_calculada),
            accent: true,
          },
        ];
      case "misto":
        return [
          { label: "Preço", value: fmtMoeda(item.preco_num) },
          { label: "Média", value: fmtNum(item.media_num) },
          {
            label: "Score",
            value: fmtNum(item.score_recomendacao),
            accent: true,
          },
        ];
      case "confronto_hibrido":
        return [
          { label: "Preço", value: fmtMoeda(item.preco_num) },
          {
            label: "Adversário",
            value: item.adversario_sigla || item.adversario_nome || "—",
          },
          {
            label: "Score",
            value: fmtNum(item.score_recomendacao),
            accent: true,
          },
        ];
      case "valorizacao":
        return [
          { label: "Preço", value: fmtMoeda(item.preco_num) },
          { label: "Mín.", value: fmtNum(item.pontos_minimos_valorizacao) },
          {
            label: "Folga",
            value: `${fmtNum(item.folga_valorizacao)} (${fmtPct(
              item.percentual_valorizacao
            )})`,
            accent: true,
          },
        ];
      default:
        return [];
    }
  }

  function renderReco(data) {
    const container = qs("#reco-resultado");
    const lista = data?.recomendacoes || [];
    if (!lista.length) {
      container.innerHTML = `
        <div class="p-8 text-center text-sm text-ink-400">
          Nenhum atleta encontrado para esse critério.
        </div>
      `;
      return;
    }
    const crit = data.criterio || criterioAtual;
    const head = `
      <thead class="bg-ink-100 text-ink-600 text-xs uppercase tracking-wide">
        <tr>
          <th class="px-3 py-2 text-left">#</th>
          <th class="px-3 py-2 text-left">Atleta</th>
          <th class="px-3 py-2 text-left">Clube</th>
          <th class="px-3 py-2 text-left">Pos.</th>
          ${cellCriterio(lista[0], crit)
            .map((c) => `<th class="px-3 py-2 text-right">${c.label}</th>`)
            .join("")}
          <th class="px-3 py-2"></th>
        </tr>
      </thead>
    `;
    const body = lista
      .map((item, idx) => {
        const cols = cellCriterio(item, crit);
        return `
          <tr class="border-t border-ink-200 hover:bg-ink-50">
            <td class="px-3 py-2 text-ink-400 text-sm">${idx + 1}</td>
            <td class="px-3 py-2 font-medium text-sm">${escapeHtml(
              item.apelido || item.nome || "—"
            )}</td>
            <td class="px-3 py-2 text-sm">
              <span class="chip">${escapeHtml(
                item.clube_sigla ||
                  item.clube_abreviacao ||
                  item.clube_nome ||
                  item.clube_id ||
                  "—"
              )}</span>
            </td>
            <td class="px-3 py-2 text-sm text-ink-500">${escapeHtml(
              item.posicao_nome || item.posicao_id || "—"
            )}</td>
            ${cols
              .map(
                (c) =>
                  `<td class="px-3 py-2 text-right text-sm ${
                    c.accent ? "font-semibold text-brand-700" : ""
                  }">${escapeHtml(c.value)}</td>`
              )
              .join("")}
            <td class="px-3 py-2 text-right">
              <button class="text-xs text-brand-700 hover:underline"
                data-ver-atleta="${item.atleta_id}">ver</button>
            </td>
          </tr>
        `;
      })
      .join("");

    const meta = RECO_CRITERIOS[crit] || {};
    container.innerHTML = `
      <div class="px-5 py-3 border-b border-ink-200 flex items-center gap-3">
        <div>
          <div class="font-semibold">${escapeHtml(meta.titulo || crit)}</div>
          <div class="text-xs text-ink-500">${escapeHtml(meta.descricao || "")}</div>
        </div>
        <div class="ml-auto text-xs text-ink-400">
          ${lista.length} atleta${lista.length === 1 ? "" : "s"}
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">${head}<tbody>${body}</tbody></table>
      </div>
    `;

    qsa("[data-ver-atleta]", container).forEach((btn) =>
      btn.addEventListener("click", () =>
        abrirFichaAtleta(Number(btn.dataset.verAtleta))
      )
    );
  }

  async function gerarRecomendacoes(ev) {
    ev.preventDefault();
    const container = qs("#reco-resultado");
    container.innerHTML = loadingBox("calculando recomendações…");
    try {
      const data = await api("/recomendacoes", paramsDoForm());
      renderReco(data);
    } catch (err) {
      showError(container, err);
    }
  }

  // -------------------- Atletas --------------------
  let searchTimer = null;
  function setupBuscaAtletas() {
    const input = qs("#atleta-search");
    input.addEventListener("input", () => {
      clearTimeout(searchTimer);
      const termo = input.value.trim();
      if (termo.length < 2) {
        qs("#atleta-resultado").innerHTML = `
          <div class="text-sm text-ink-400">Digite ao menos 2 caracteres.</div>
        `;
        return;
      }
      searchTimer = setTimeout(() => buscarAtletas(termo), 300);
    });
  }

  async function buscarAtletas(nome) {
    const box = qs("#atleta-resultado");
    box.innerHTML = loadingBox("buscando…");
    try {
      const data = await api("/atletas/buscar", { nome });
      const lista = data?.atletas || data?.resultados || [];
      if (!lista.length) {
        box.innerHTML = `<div class="text-sm text-ink-400">Nenhum atleta encontrado.</div>`;
        return;
      }
      box.innerHTML = `
        <div class="bg-white rounded-xl border border-ink-200 overflow-hidden">
          <table class="w-full">
            <thead class="bg-ink-100 text-ink-600 text-xs uppercase tracking-wide">
              <tr>
                <th class="px-3 py-2 text-left">Atleta</th>
                <th class="px-3 py-2 text-left">Clube</th>
                <th class="px-3 py-2 text-left">Pos.</th>
                <th class="px-3 py-2 text-right">Preço</th>
                <th class="px-3 py-2 text-right">Média</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              ${lista
                .map(
                  (a) => `
                <tr class="border-t border-ink-200 hover:bg-ink-50">
                  <td class="px-3 py-2 font-medium text-sm">${escapeHtml(
                    a.apelido || a.nome || "—"
                  )}</td>
                  <td class="px-3 py-2 text-sm">
                    <span class="chip">${escapeHtml(
                      a.clube_sigla ||
                        a.clube_abreviacao ||
                        state.clubesPorId[a.clube_id]?.abreviacao ||
                        state.clubesPorId[a.clube_id]?.nome ||
                        a.clube_id ||
                        "—"
                    )}</span>
                  </td>
                  <td class="px-3 py-2 text-sm text-ink-500">${escapeHtml(
                    a.posicao_nome || a.posicao_id || "—"
                  )}</td>
                  <td class="px-3 py-2 text-right text-sm">${fmtMoeda(
                    a.preco_num
                  )}</td>
                  <td class="px-3 py-2 text-right text-sm">${fmtNum(
                    a.media_num
                  )}</td>
                  <td class="px-3 py-2 text-right">
                    <button class="text-xs text-brand-700 hover:underline"
                      data-ver-atleta="${a.atleta_id}">ver ficha</button>
                  </td>
                </tr>
              `
                )
                .join("")}
            </tbody>
          </table>
        </div>
      `;
      qsa("[data-ver-atleta]", box).forEach((btn) =>
        btn.addEventListener("click", () =>
          abrirFichaAtleta(Number(btn.dataset.verAtleta))
        )
      );
    } catch (err) {
      showError(box, err);
    }
  }

  async function abrirFichaAtleta(atletaId) {
    openModal(`Atleta #${atletaId}`, loadingBox("carregando ficha…"));
    try {
      const [ficha, historico, tendencia] = await Promise.all([
        api(`/atletas/${atletaId}`).catch(() => null),
        api(`/historico/atleta/${atletaId}`, { rodadas: 5 }).catch(() => null),
        api(`/tendencia/atleta/${atletaId}`, { rodadas: 6 }).catch(() => null),
      ]);

      const a = ficha?.atleta || ficha || {};
      const hist = historico?.historico || [];
      const tend = tendencia?.tendencia || tendencia || {};

      const linhasHist = hist.length
        ? hist
            .map(
              (r) => `
            <tr class="border-t border-ink-200">
              <td class="px-3 py-1.5 text-sm">${escapeHtml(r.rodada ?? "—")}</td>
              <td class="px-3 py-1.5 text-sm">${r.entrou_em_campo ? "✓" : "—"}</td>
              <td class="px-3 py-1.5 text-right text-sm">${fmtNum(r.pontuacao_cartola)}</td>
              <td class="px-3 py-1.5 text-right text-sm">${fmtNum(r.pontuacao_calculada)}</td>
            </tr>`
            )
            .join("")
        : `<tr><td class="p-3 text-sm text-ink-400" colspan="4">sem histórico disponível</td></tr>`;

      const direcao = tend?.direcao || tend?.tendencia;
      const chipTend =
        direcao === "subindo"
          ? `<span class="chip chip-green">↑ subindo</span>`
          : direcao === "caindo"
          ? `<span class="chip chip-red">↓ caindo</span>`
          : direcao === "estavel"
          ? `<span class="chip chip-amber">→ estável</span>`
          : `<span class="chip">sem tendência</span>`;

      const html = `
        <div class="flex items-start gap-4 mb-4">
          <div class="w-14 h-14 rounded-full bg-ink-100 grid place-items-center text-xl font-bold text-ink-600">
            ${escapeHtml((a.apelido || "?").charAt(0))}
          </div>
          <div class="flex-1">
            <div class="font-bold text-lg">${escapeHtml(a.apelido || a.nome || "—")}</div>
            <div class="text-sm text-ink-500">
              ${escapeHtml(a.posicao_nome || a.posicao_id || "")} ·
              <span class="chip">${escapeHtml(
                a.clube_sigla ||
                  a.clube_abreviacao ||
                  state.clubesPorId[a.clube_id]?.abreviacao ||
                  a.clube_id ||
                  "—"
              )}</span>
            </div>
            <div class="mt-2 flex gap-4 text-sm">
              <div><span class="text-ink-400">Preço:</span> <b>${fmtMoeda(a.preco_num)}</b></div>
              <div><span class="text-ink-400">Média:</span> <b>${fmtNum(a.media_num)}</b></div>
              <div>${chipTend}</div>
            </div>
          </div>
        </div>

        <h3 class="font-semibold text-sm mt-4 mb-1">Tendência</h3>
        <div class="text-sm text-ink-600 bg-ink-50 rounded-lg p-3 mb-4">
          ${tend?.media_recente != null ? `Média recente: <b>${fmtNum(tend.media_recente)}</b>` : ""}
          ${tend?.oscilacao != null ? ` · Oscilação: <b>${fmtNum(tend.oscilacao)}</b>` : ""}
          ${tend?.rodadas_validas != null ? ` · Rodadas válidas: <b>${tend.rodadas_validas}</b>` : ""}
        </div>

        <h3 class="font-semibold text-sm mb-1">Histórico (últimas rodadas)</h3>
        <div class="overflow-x-auto border border-ink-200 rounded-lg">
          <table class="w-full">
            <thead class="bg-ink-100 text-ink-600 text-xs uppercase">
              <tr>
                <th class="px-3 py-1.5 text-left">Rodada</th>
                <th class="px-3 py-1.5 text-left">Jogou</th>
                <th class="px-3 py-1.5 text-right">Pts Cartola</th>
                <th class="px-3 py-1.5 text-right">Pts Calc.</th>
              </tr>
            </thead>
            <tbody>${linhasHist}</tbody>
          </table>
        </div>
      `;
      openModal(`${a.apelido || "Atleta"} — #${a.atleta_id ?? atletaId}`, html);
    } catch (err) {
      openModal(
        "Erro",
        `<div class="text-sm text-red-700">${escapeHtml(err.message)}</div>`
      );
    }
  }

  // -------------------- Clubes --------------------
  async function carregarClubes() {
    const box = qs("#clubes-resultado");
    box.innerHTML = `<div class="col-span-full text-center text-sm text-ink-400 py-8"><span class="spinner"></span> carregando clubes…</div>`;
    try {
      const data = await api("/clubes");
      // A API /clubes retorna um objeto indexado por id (ex.: {"262": {...}})
      // Tambem aceitamos {clubes: [...]} ou array direto por robustez.
      const lista = Array.isArray(data)
        ? data
        : Array.isArray(data?.clubes)
        ? data.clubes
        : data && typeof data === "object"
        ? Object.values(data)
        : [];
      // indexa pra uso em outras telas
      state.clubesLista = lista;
      state.clubesPorId = lista.reduce((acc, c) => {
        const key = c.clube_id ?? c.id;
        if (key != null) acc[key] = c;
        return acc;
      }, {});
      state.clubesCarregados = true;
      renderClubes();
    } catch (err) {
      showError(box, err);
    }
  }

  function filtrarClubes(lista, filtro) {
    const termo = normalize(filtro);
    if (!termo) return lista;
    return lista.filter((c) => {
      const campos = [
        c.nome,
        c.abreviacao,
        c.slug,
        c.nome_fantasia,
        String(c.clube_id ?? c.id ?? ""),
      ];
      return campos.some((v) => normalize(v).includes(termo));
    });
  }

  function renderClubes() {
    const box = qs("#clubes-resultado");
    const contador = qs("#clubes-contador");
    const filtrada = filtrarClubes(state.clubesLista, state.clubeFiltro);

    contador.textContent = state.clubeFiltro
      ? `${filtrada.length} de ${state.clubesLista.length}`
      : `${state.clubesLista.length} clubes`;

    if (!filtrada.length) {
      box.innerHTML = `
        <div class="col-span-full text-center text-sm text-ink-400 py-8">
          Nenhum clube encontrado${
            state.clubeFiltro ? ` para "${escapeHtml(state.clubeFiltro)}"` : ""
          }.
        </div>
      `;
      return;
    }

    box.innerHTML = filtrada
      .map(
        (c) => `
          <button
            class="bg-white rounded-xl border border-ink-200 p-4 text-left hover:border-brand-500 hover:shadow-sm transition"
            data-clube-id="${c.clube_id ?? c.id}"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-ink-100 grid place-items-center text-sm font-bold text-ink-600">
                ${escapeHtml((c.abreviacao || c.nome || "?").slice(0, 3))}
              </div>
              <div class="min-w-0">
                <div class="font-semibold text-sm truncate">${escapeHtml(c.nome || "—")}</div>
                <div class="text-xs text-ink-400">${escapeHtml(c.abreviacao || c.slug || "")}</div>
              </div>
            </div>
          </button>
        `
      )
      .join("");

    qsa("[data-clube-id]", box).forEach((btn) =>
      btn.addEventListener("click", () =>
        abrirDetalheClube(Number(btn.dataset.clubeId))
      )
    );
  }

  function setupBuscaClubes() {
    const input = qs("#clube-search");
    if (!input) return;
    input.addEventListener("input", () => {
      state.clubeFiltro = input.value;
      if (state.clubesCarregados) renderClubes();
    });
  }

  async function abrirDetalheClube(clubeId) {
    openModal(`Clube #${clubeId}`, loadingBox("carregando clube…"));
    try {
      const [clubeData, elencoData] = await Promise.all([
        api(`/clubes/${clubeId}`),
        api(`/atletas/clube/${clubeId}`).catch(() => ({ atletas: [] })),
      ]);
      const c = clubeData?.clube || clubeData || {};
      const atletas = elencoData?.atletas || [];

      const linhasAtletas = atletas.length
        ? atletas
            .map(
              (a) => `
                <tr class="border-t border-ink-200 hover:bg-ink-50">
                  <td class="px-3 py-1.5 text-sm font-medium">${escapeHtml(
                    a.apelido || a.nome || "—"
                  )}</td>
                  <td class="px-3 py-1.5 text-sm text-ink-500">${escapeHtml(
                    a.posicao_nome || a.posicao_id || "—"
                  )}</td>
                  <td class="px-3 py-1.5 text-right text-sm">${fmtMoeda(a.preco_num)}</td>
                  <td class="px-3 py-1.5 text-right text-sm">${fmtNum(a.media_num)}</td>
                  <td class="px-3 py-1.5 text-right">
                    <button class="text-xs text-brand-700 hover:underline"
                      data-ver-atleta="${a.atleta_id}">ver</button>
                  </td>
                </tr>`
            )
            .join("")
        : `<tr><td colspan="5" class="p-3 text-sm text-ink-400 text-center">
             Nenhum atleta encontrado no mercado atual para este clube.
           </td></tr>`;

      const html = `
        <div class="flex items-center gap-4 mb-4">
          <div class="w-16 h-16 rounded-full bg-ink-100 grid place-items-center text-lg font-bold text-ink-600">
            ${escapeHtml((c.abreviacao || c.nome || "?").slice(0, 3))}
          </div>
          <div>
            <div class="text-xl font-bold">${escapeHtml(c.nome || "—")}</div>
            <div class="text-sm text-ink-500">
              ${escapeHtml(c.abreviacao || "")}${c.slug ? " · " + escapeHtml(c.slug) : ""}
            </div>
          </div>
          <div class="ml-auto text-xs text-ink-400">
            ${atletas.length} atleta${atletas.length === 1 ? "" : "s"}
          </div>
        </div>

        <h3 class="font-semibold text-sm mb-1">Elenco no mercado</h3>
        <div class="overflow-x-auto border border-ink-200 rounded-lg mb-4">
          <table class="w-full">
            <thead class="bg-ink-100 text-ink-600 text-xs uppercase">
              <tr>
                <th class="px-3 py-1.5 text-left">Atleta</th>
                <th class="px-3 py-1.5 text-left">Pos.</th>
                <th class="px-3 py-1.5 text-right">Preço</th>
                <th class="px-3 py-1.5 text-right">Média</th>
                <th class="px-3 py-1.5"></th>
              </tr>
            </thead>
            <tbody>${linhasAtletas}</tbody>
          </table>
        </div>

        <details class="text-xs text-ink-500">
          <summary class="cursor-pointer select-none">Dados brutos do clube</summary>
          <pre class="text-xs bg-ink-50 border border-ink-200 rounded-lg p-3 overflow-x-auto mt-2">${escapeHtml(
            JSON.stringify(c, null, 2)
          )}</pre>
        </details>
      `;
      openModal(c.nome || `Clube #${clubeId}`, html);

      qsa("[data-ver-atleta]", qs("#modal-body")).forEach((btn) =>
        btn.addEventListener("click", () =>
          abrirFichaAtleta(Number(btn.dataset.verAtleta))
        )
      );
    } catch (err) {
      openModal(
        "Erro",
        `<div class="text-sm text-red-700">${escapeHtml(err.message)}</div>`
      );
    }
  }

  // -------------------- Modal --------------------
  function openModal(titulo, html) {
    qs("#modal-title").textContent = titulo;
    qs("#modal-body").innerHTML = html;
    const modal = qs("#modal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");
  }
  function closeModal() {
    const modal = qs("#modal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
  }

  // -------------------- init --------------------
  function init() {
    qsa("#nav-tabs .tab-btn").forEach((btn) =>
      btn.addEventListener("click", () => setRoute(btn.dataset.route))
    );
    window.addEventListener("hashchange", onRouteChange);

    setupRecoTabs();
    qs("#reco-form").addEventListener("submit", gerarRecomendacoes);

    setupBuscaAtletas();
    setupBuscaClubes();

    qs("#modal-close").addEventListener("click", closeModal);
    qs("#modal").addEventListener("click", (ev) => {
      if (ev.target.id === "modal") closeModal();
    });

    carregarStatusMercado();
    onRouteChange();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
