// Test DOM headless du bloc « Performance — Non coté (PE) », version allégée (23/07/2026) :
// Widgets : 1) bandeau KPI MOIC/TVPI · 4) détail par contrat en accordéon.
// Les anciens widgets 2 (graphe trimestriel) et 3 (composition multiples) ont été SUPPRIMÉS
// à la demande du CGP — le test vérifie leur ABSENCE.
// Usage : npm i jsdom && node test_pnc.mjs <reporting.html>
// Le HTML doit être rendu depuis fx_simple.xlsx (les valeurs attendues en dépendent).
import { JSDOM } from "jsdom";
import fs from "fs";

const html = fs.readFileSync(process.argv[2] || "/tmp/demo_simple.html", "utf-8");
const dom = new JSDOM(html, { runScripts: "outside-only" });
const { window } = dom;
const { document } = window;

// Stub Chart.js (le CDN n'est pas chargé en headless)
window.HTMLCanvasElement.prototype.getContext = () => ({});
let updates = 0;
window.Chart = class {
  constructor(ctx, cfg){ this.data = cfg.data; this.options = cfg.options; }
  update(){ updates++; }
  resize(){}
};

// Rejouer les scripts inline (jsdom outside-only ne les exécute pas)
for (const sc of document.querySelectorAll("script:not([src])")) {
  try { window.eval(sc.textContent); }
  catch (e) { /* scripts décoratifs (ex. animation Hero via currentScript) hors périmètre du test */ }
}

const q = s => document.querySelector(`[data-pnc="${s}"]`);
const assert = (c, msg) => { if (!c) { console.error("✗ " + msg); process.exitCode = 1; } else console.log("✓ " + msg); };

// ── Widget 1 — bandeau KPI (état initial = portefeuille) ──
// valeur corrigée : Tikehau (aucun flux ni date d'investissement) n'est plus imputé
// à sa valeur courante sur des trimestres antérieurs à toute preuve d'existence (fix "invente de la data").
// 670 000 = Altaroc (150 000, valo 20/12/2025) + Essling (520 000, valo 31/12/2025) ; Tikehau exclu au T4-25.
assert(q("k-start").innerHTML.includes("670 000"), "KPI valeur début = 670 000 € (T4-25, Tikehau exclu avant sa 1re preuve)");
assert(q("k-value").innerHTML.includes("1 829 000"), "KPI valeur fin (base TVPI) = 1 829 000 €");
assert(q("moic-mult").textContent.includes("×"), "carte MOIC : multiple affiché (×)");
assert(q("tvpi-mult").textContent.includes("×"), "carte TVPI : multiple affiché (×)");
assert(/€/.test(q("moic-sub").textContent) && /%/.test(q("moic-sub").textContent), "carte MOIC : € et % en sous-titre");
assert(/€/.test(q("tvpi-sub").textContent) && /%/.test(q("tvpi-sub").textContent), "carte TVPI : € et % en sous-titre");
// ── Widgets 2 & 3 supprimés : vérifier leur absence ──
assert(document.querySelector('#perf_nc_bars') === null, "PE : graphe trimestriel supprimé");
assert(document.querySelectorAll('[data-pnc-view]').length === 0, "PE : composition multiples supprimée");
assert(document.querySelector('.pnc-mlegend') === null, "PE : légende MOIC/TVPI supprimée");

// ── Widget 4 — détail par contrat en accordéon ──
const w4 = document.querySelector('.nc-acc-tbl');
assert(w4 !== null, "détail par contrat : tableau accordéon présent");
const head = w4.textContent;
for (const col of ["Cap. engagé","Cap. appelé","Non appelé réel","Non appelé estimé","MOIC","Valeur (dern. constat.)"])
  assert(head.includes(col), `détail : colonne ${col}`);
assert(head.includes("TOTAL"), "détail : ligne TOTAL");
const acc0 = w4.querySelector('.acc-head.acc-clickable');
assert(acc0 !== null, "détail : ligne dépliable");
const det0 = acc0.nextElementSibling;
assert(det0.hidden === true, "détail : dépliant caché par défaut");
acc0.click();
assert(det0.hidden === false, "détail : dépliant ouvert au clic");
assert(/Appel prévu/.test(det0.textContent) && /15\/09\/2026/.test(det0.textContent), "détail : échéancier prévisionnel (appel Altaroc 15/09/2026)");
assert(/TVPI/.test(det0.textContent) && /DPI/.test(det0.textContent) && /TRI/.test(det0.textContent), "détail : stats TVPI/DPI/TRI dans le dépliant");

// glossaire + pitch commercial
const gloss = document.querySelector('.nc-acc-tbl') && document.querySelectorAll('.pnc-gloss');
assert([...document.querySelectorAll('.pnc-gloss')].some(g=>/TVPI/.test(g.textContent)&&/DPI/.test(g.textContent)&&/TRI/.test(g.textContent)), "glossaire TVPI/DPI/TRI présent");
assert(document.querySelector('.pnc-pitch') === null, "pitch commercial retiré avec la composition");

console.log(process.exitCode ? "\nÉCHECS" : "\nTOUT OK");
