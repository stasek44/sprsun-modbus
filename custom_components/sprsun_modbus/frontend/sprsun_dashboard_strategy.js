/**
 * SPRSUN Heat Pump — Native Lovelace Dashboard & Section Strategies.
 *
 * Single-source template + i18n JSON architecture:
 * - Resolves UI language automatically from `hass.locale.language` (pl / en).
 * - Resolves exact user entity_ids via `sprsun_modbus/get_dashboard_context`
 *   using unique_id keys (works with renamed devices and translated entity names).
 * - Selects controller-specific template (`chico`, etc.).
 */

const BASE_URL = new URL(".", import.meta.url).href;
const VERSION_QUERY = new URL(import.meta.url).search || "";

const TRANSLATION_TOKEN_RE = /\[\[t:([a-z0-9_]+)\]\]/g;
const ENTITY_TOKEN_RE = /\[\[ent:([a-z_]+):([a-z0-9_]+)\]\]/g;

const _jsonCache = new Map();

async function fetchJsonCached(relativePath) {
  const url = `${BASE_URL}${relativePath}${VERSION_QUERY}`;
  if (_jsonCache.has(url)) {
    return _jsonCache.get(url);
  }
  const resp = await fetch(url, { credentials: "same-origin" });
  if (!resp.ok) {
    throw new Error(`Failed to fetch ${relativePath}: HTTP ${resp.status}`);
  }
  const data = await resp.json();
  _jsonCache.set(url, data);
  return data;
}

function normalizeLanguage(rawLang) {
  if (!rawLang || typeof rawLang !== "string") {
    return "en";
  }
  const base = rawLang.toLowerCase().split(/[-_]/)[0].trim();
  return base || "en";
}

async function loadTranslations(lang) {
  const enPromise = fetchJsonCached("i18n/en.json");
  if (lang === "en") {
    const en = await enPromise;
    return { active: en, fallback: en };
  }
  try {
    const [active, fallback] = await Promise.all([
      fetchJsonCached(`i18n/${lang}.json`),
      enPromise,
    ]);
    return { active, fallback };
  } catch {
    const en = await enPromise;
    return { active: en, fallback: en };
  }
}

async function fetchDashboardContext(hass, entryId) {
  const payload = { type: "sprsun_modbus/get_dashboard_context" };
  if (entryId) {
    payload.entry_id = entryId;
  }
  try {
    return await hass.callWS(payload);
  } catch {
    return {
      entry_id: null,
      title: "SPRSUN Heat Pump",
      controller_type: "chico",
      enable_derived_sensors: false,
      enable_expert_writes: false,
      entities: {},
      entries: [],
    };
  }
}

function getTranslated(translations, key) {
  if (key in translations.active) {
    return translations.active[key];
  }
  if (key in translations.fallback) {
    return translations.fallback[key];
  }
  return key;
}

function resolveString(str, translations, entityMap) {
  const withText = str.replace(TRANSLATION_TOKEN_RE, (_match, key) =>
    getTranslated(translations, key)
  );

  return withText.replace(ENTITY_TOKEN_RE, (_match, domain, key) => {
    const lookupKey = `${domain}:${key}`;
    if (lookupKey in entityMap) {
      return entityMap[lookupKey];
    }
    return `${domain}.sprsun_heat_pump_${key}`;
  });
}

function makeNoticeCard(text) {
  return {
    type: "markdown",
    text_only: true,
    content: text,
  };
}

function filterCardNode(card, hiddenSet) {
  if (!card || typeof card !== "object") {
    return card;
  }
  if (typeof card.entity === "string" && hiddenSet.has(card.entity)) {
    return null;
  }
  if (card.type === "history-graph" && Array.isArray(card.entities)) {
    const kept = card.entities.filter((item) => {
      const eid = typeof item === "string" ? item : item?.entity;
      return !eid || !hiddenSet.has(eid);
    });
    if (kept.length === 0) {
      return null;
    }
    return { ...card, entities: kept };
  }
  if (Array.isArray(card.cards)) {
    const kept = card.cards
      .map((child) => filterCardNode(child, hiddenSet))
      .filter(Boolean);
    if (kept.length === 0) {
      return null;
    }
    return { ...card, cards: kept };
  }
  if (card.type === "conditional" && card.card) {
    const inner = filterCardNode(card.card, hiddenSet);
    if (!inner) {
      return null;
    }
    return { ...card, card: inner };
  }
  return card;
}

function sectionUsesHiddenEntity(section, hiddenSet) {
  if (!Array.isArray(section?.visibility)) {
    return false;
  }
  return section.visibility.some(
    (cond) => typeof cond?.entity === "string" && hiddenSet.has(cond.entity)
  );
}

function applyOptionalEntityNotices(views, context, translations) {
  const hasEntry = Boolean(context.entry_id);
  const derivedOff = hasEntry && context.enable_derived_sensors === false;
  const expertOff = hasEntry && context.enable_expert_writes === false;

  const hiddenSet = new Set([
    ...(derivedOff ? context.derived_entity_ids || [] : []),
    ...(expertOff ? context.expert_entity_ids || [] : []),
  ]);

  const filteredAmb = context.entities?.["sensor:ambient_temp_filtered"];
  const rawAmb = context.entities?.["sensor:ambient_temp"];

  const derivedNotice = getTranslated(
    translations,
    "notice_derived_sensors_disabled"
  );
  const expertNotice = getTranslated(
    translations,
    "notice_expert_writes_disabled"
  );

  return views.map((view, viewIdx) => {
    const nextView = { ...view };

    if (Array.isArray(view.badges)) {
      nextView.badges = view.badges
        .map((badge) => {
          if (derivedOff && filteredAmb && rawAmb && badge?.entity === filteredAmb) {
            return { ...badge, entity: rawAmb };
          }
          if (badge?.entity && hiddenSet.has(badge.entity)) {
            return null;
          }
          return badge;
        })
        .filter(Boolean);
    }

    if (!Array.isArray(view.sections)) {
      return nextView;
    }

    const nextSections = view.sections
      .filter((sec) => !sectionUsesHiddenEntity(sec, hiddenSet))
      .map((sec, secIdx) => {
        let cards = (sec.cards || [])
          .map((c) => filterCardNode(c, hiddenSet))
          .filter(Boolean);

        if (derivedOff && secIdx === 0 && (viewIdx === 0 || viewIdx === 1 || viewIdx === 2)) {
          const insertAt = Math.min(2, cards.length);
          cards = [
            ...cards.slice(0, insertAt),
            makeNoticeCard(derivedNotice),
            ...cards.slice(insertAt),
          ];
        }

        if (derivedOff && viewIdx === 3 && secIdx === 0) {
          const mdIdx = cards.findIndex((c) => c.type === "markdown");
          if (mdIdx >= 0) {
            cards = [
              ...cards.slice(0, mdIdx),
              makeNoticeCard(derivedNotice),
              ...cards.slice(mdIdx + 1),
            ];
          } else {
            cards.push(makeNoticeCard(derivedNotice));
          }
        }

        return { ...sec, cards };
      });

    if (expertOff && viewIdx === 3) {
      nextSections.push({
        type: "grid",
        column_span: 2,
        cards: [makeNoticeCard(expertNotice)],
      });
    }

    nextView.sections = nextSections;
    return nextView;
  });
}

function renderTemplateNode(node, translations, entityMap) {
  if (typeof node === "string") {
    return resolveString(node, translations, entityMap);
  }
  if (Array.isArray(node)) {
    return node.map((item) => renderTemplateNode(item, translations, entityMap));
  }
  if (node !== null && typeof node === "object") {
    const out = {};
    for (const [k, v] of Object.entries(node)) {
      out[k] = renderTemplateNode(v, translations, entityMap);
    }
    return out;
  }
  return node;
}

function buildGenericFallbackDashboard(context, lang) {
  const isPl = lang === "pl";
  const allEntities = Object.values(context.entities || {}).slice(0, 60);
  return {
    title: context.title || "SPRSUN Heat Pump",
    views: [
      {
        type: "sections",
        title: context.title || "SPRSUN",
        path: "sprsun",
        icon: "mdi:heat-pump",
        sections: [
          {
            type: "grid",
            cards: [
              {
                type: "heading",
                heading: isPl
                  ? `Sterownik ${String(context.controller_type || "").toUpperCase()}`
                  : `${String(context.controller_type || "").toUpperCase()} Controller`,
                heading_style: "title",
                icon: "mdi:heat-pump",
              },
              ...allEntities.map((entity) => ({
                type: "tile",
                entity,
              })),
            ],
          },
        ],
      },
    ],
  };
}

class SprsunDashboardStrategy extends HTMLElement {
  static async generate(config, hass) {
    const opts = config?.strategy || config || {};
    const lang = normalizeLanguage(
      opts.language || hass?.locale?.language || hass?.language
    );

    const [context, translations] = await Promise.all([
      fetchDashboardContext(hass, opts.entry_id),
      loadTranslations(lang),
    ]);

    const controllerType = (context.controller_type || "chico").toLowerCase();
    let template;
    try {
      template = await fetchJsonCached(
        `sprsun_dashboard_${controllerType}.json`
      );
    } catch {
      return buildGenericFallbackDashboard(context, lang);
    }

    const rendered = renderTemplateNode(
      template,
      translations,
      context.entities || {}
    );
    const views = applyOptionalEntityNotices(
      rendered.views || [],
      context,
      translations
    );
    return {
      title:
        opts.title ||
        context.title ||
        translations.active.strategy_dashboard_title ||
        "SPRSUN Heat Pump",
      views,
    };
  }

  static async getStubConfig() {
    return {};
  }
}

class SprsunControlSectionStrategy extends HTMLElement {
  static async generate(config, hass) {
    const opts = config?.strategy || config || {};
    const lang = normalizeLanguage(
      opts.language || hass?.locale?.language || hass?.language
    );

    const [context, translations] = await Promise.all([
      fetchDashboardContext(hass, opts.entry_id),
      loadTranslations(lang),
    ]);

    const controllerType = (context.controller_type || "chico").toLowerCase();
    let template;
    try {
      template = await fetchJsonCached(
        `sprsun_control_card_${controllerType}.json`
      );
    } catch {
      return {
        cards: Object.values(context.entities || {})
          .slice(0, 12)
          .map((entity) => ({ type: "tile", entity })),
      };
    }

    const renderedCard = renderTemplateNode(
      template,
      translations,
      context.entities || {}
    );
    const derivedOff =
      Boolean(context.entry_id) && context.enable_derived_sensors === false;
    if (!derivedOff) {
      return {
        cards: [renderedCard],
      };
    }

    const hiddenSet = new Set(context.derived_entity_ids || []);
    const filteredCard = filterCardNode(renderedCard, hiddenSet);
    const cards = filteredCard ? [filteredCard] : [];
    cards.push(
      makeNoticeCard(
        getTranslated(translations, "notice_derived_sensors_disabled")
      )
    );
    return { cards };
  }

  static async getStubConfig() {
    return {};
  }
}

if (!customElements.get("ll-strategy-dashboard-sprsun")) {
  customElements.define(
    "ll-strategy-dashboard-sprsun",
    SprsunDashboardStrategy
  );
}

if (!customElements.get("ll-strategy-section-sprsun-control")) {
  customElements.define(
    "ll-strategy-section-sprsun-control",
    SprsunControlSectionStrategy
  );
}

const PICKER_META = {
  en: {
    dashName: "SPRSUN Heat Pump",
    dashDesc: "Ready-to-use 4-tab SPRSUN heat pump dashboard with automatic language & entity detection.",
    secName: "SPRSUN — Quick Control",
    secDesc: "Compact SPRSUN heat pump control section for any dashboard.",
  },
  pl: {
    dashName: "Pompa Ciepła SPRSUN",
    dashDesc: "Gotowy 4-zakładkowy dashboard pompy ciepła SPRSUN z automatycznym językiem i wykrywaniem encji.",
    secName: "SPRSUN — Sterowanie",
    secDesc: "Kompaktowa sekcja sterowania pompą SPRSUN na dowolny pulpit.",
  },
  fr: {
    dashName: "Pompe à chaleur SPRSUN",
    dashDesc: "Tableau de bord SPRSUN à 4 onglets prêt à l'emploi avec détection automatique de la langue et des entités.",
    secName: "SPRSUN — Contrôle rapide",
    secDesc: "Section de contrôle compacte SPRSUN pour tout tableau de bord.",
  },
  de: {
    dashName: "SPRSUN Wärmepumpe",
    dashDesc: "Sofort einsatzbereites 4-Tab-Dashboard mit automatischer Sprach- und Entitätserkennung.",
    secName: "SPRSUN — Schnellsteuerung",
    secDesc: "Kompakter SPRSUN-Steuerungsbereich für jedes Dashboard.",
  },
  es: {
    dashName: "Bomba de calor SPRSUN",
    dashDesc: "Panel SPRSUN de 4 pestañas listo para usar con detección automática de idioma y entidades.",
    secName: "SPRSUN — Control rápido",
    secDesc: "Sección compacta de control SPRSUN para cualquier panel.",
  },
  cs: {
    dashName: "Tepelné čerpadlo SPRSUN",
    dashDesc: "Připravený 4-kartový dashboard SPRSUN s automatickým jazykem a rozpoznáním entit.",
    secName: "SPRSUN — Rychlé ovládání",
    secDesc: "Kompaktní ovládací sekce SPRSUN pro libovolný dashboard.",
  },
  sk: {
    dashName: "Tepelné čerpadlo SPRSUN",
    dashDesc: "Pripravený 4-kartový dashboard SPRSUN s automatickým jazykom a rozpoznaním entít.",
    secName: "SPRSUN — Rýchle ovládanie",
    secDesc: "Kompaktná ovládacia sekcia SPRSUN pre ľubovoľný dashboard.",
  },
  hu: {
    dashName: "SPRSUN Hőszivattyú",
    dashDesc: "Azonnal használható 4 lapos SPRSUN irányítópult automatikus nyelv- és entitásfelismeréssel.",
    secName: "SPRSUN — Gyorsvezérlés",
    secDesc: "Kompakt SPRSUN vezérlő szakasz bármely irányítópulthoz.",
  },
  lt: {
    dashName: "SPRSUN Šilumos siurblys",
    dashDesc: "Paruoštas 4 skirtukų SPRSUN skydelis su automatiniu kalbos ir objektų atpažinimu.",
    secName: "SPRSUN — Greitas valdymas",
    secDesc: "Kompaktiška SPRSUN valdymo sekcija bet kuriam skydeliui.",
  },
  uk: {
    dashName: "Тепловий насос SPRSUN",
    dashDesc: "Готова 4-вкладкова панель SPRSUN з автоматичним визначенням мови та сутностей.",
    secName: "SPRSUN — Швидке керування",
    secDesc: "Компактна секція керування SPRSUN для будь-якої панелі.",
  },
};

const browserLang = normalizeLanguage(
  typeof navigator !== "undefined" ? navigator.language : "en"
);
const pickerText = PICKER_META[browserLang] || PICKER_META.en;

window.customStrategies = window.customStrategies || [];

if (!window.customStrategies.some((item) => item?.type === "sprsun")) {
  window.customStrategies.push({
    type: "sprsun",
    strategyType: "dashboard",
    name: pickerText.dashName,
    description: pickerText.dashDesc,
    documentationURL: "https://github.com/stasek44/sprsun-modbus/blob/main/docs/DASHBOARD.md",
  });
}

if (!window.customStrategies.some((item) => item?.type === "sprsun-control")) {
  window.customStrategies.push({
    type: "sprsun-control",
    strategyType: "section",
    name: pickerText.secName,
    description: pickerText.secDesc,
    documentationURL: "https://github.com/stasek44/sprsun-modbus/blob/main/docs/DASHBOARD.md",
  });
}
