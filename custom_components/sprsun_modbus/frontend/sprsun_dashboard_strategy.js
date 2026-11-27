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

function resolveString(str, translations, entityMap) {
  const withText = str.replace(TRANSLATION_TOKEN_RE, (_match, key) => {
    if (key in translations.active) {
      return translations.active[key];
    }
    if (key in translations.fallback) {
      return translations.fallback[key];
    }
    return key;
  });

  return withText.replace(ENTITY_TOKEN_RE, (_match, domain, key) => {
    const lookupKey = `${domain}:${key}`;
    if (lookupKey in entityMap) {
      return entityMap[lookupKey];
    }
    return `${domain}.sprsun_heat_pump_${key}`;
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
    return {
      title:
        opts.title ||
        context.title ||
        translations.active.strategy_dashboard_title ||
        "SPRSUN Heat Pump",
      views: rendered.views || [],
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
    return {
      cards: [renderedCard],
    };
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

const isBrowserPl =
  typeof navigator !== "undefined" &&
  String(navigator.language || "").toLowerCase().startsWith("pl");

window.customStrategies = window.customStrategies || [];

if (!window.customStrategies.some((item) => item?.type === "sprsun")) {
  window.customStrategies.push({
    type: "sprsun",
    strategyType: "dashboard",
    name: isBrowserPl ? "Pompa Ciepła SPRSUN" : "SPRSUN Heat Pump",
    description: isBrowserPl
      ? "Gotowy 4-zakładkowy dashboard pompy ciepła SPRSUN z automatycznym językiem i wykrywaniem encji."
      : "Ready-to-use 4-tab SPRSUN heat pump dashboard with automatic language & entity detection.",
    documentationURL: "https://github.com/stasek44/sprsun-modbus/blob/main/docs/DASHBOARD.md",
  });
}

if (!window.customStrategies.some((item) => item?.type === "sprsun-control")) {
  window.customStrategies.push({
    type: "sprsun-control",
    strategyType: "section",
    name: isBrowserPl ? "SPRSUN — Sterowanie" : "SPRSUN — Quick Control",
    description: isBrowserPl
      ? "Kompaktowa sekcja sterowania pompą SPRSUN na dowolny pulpit."
      : "Compact SPRSUN heat pump control section for any dashboard.",
    documentationURL: "https://github.com/stasek44/sprsun-modbus/blob/main/docs/DASHBOARD.md",
  });
}
