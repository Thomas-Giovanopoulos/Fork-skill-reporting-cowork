// Test DOM headless du bloc « Performance — Non coté (PE) » :
// Widgets : 1) bandeau KPI MOIC/TVPI · 2) graphe trimestriel · 3) composition multiples · 4) détail accordéon.
// Historique : les widgets 2 et 3 avaient été SUPPRIMÉS le 23/07/2026 à la demande du CGP,
// puis RÉTABLIS le 30/07/2026 sur arbitrage explicite de Thomas (chantier UI, D-UI-1) —
// le test, qui vérifiait leur absence, a été RETOURNÉ : il vérifie désormais leur PRÉSENCE
// et exerce la bascule de vue par fonds.
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
// ── Widgets 2 & 3 rétablis (30/07/2026) : présence + bascule de vue ──
assert(document.querySelector('#perf_nc_bars') !== null, "W2 : canvas graphe trimestriel présent");
const rows = document.querySelectorAll('[data-pnc-view]');
assert(rows.length >= 2, `W3 : composition cliquable (${rows.length} vues : portefeuille + fonds)`);
assert(document.querySelector('.pnc-mlegend') !== null, "W3 : légende MOIC/TVPI/Cible présente");
assert(/Valorisation trimestrielle/.test((q("chart-title")||{}).textContent||""), "W2 : titre du graphe présent");
assert(document.querySelector('[data-pnc-view].pnc-active') === rows[0], "W3 : vue portefeuille active par défaut");
// bascule : cliquer la 2e vue → chart.update() appelé, KPI et surbrillance suivent
const before = q("k-start").textContent;
rows[1].click();
assert(updates >= 1, "bascule : chart.update() déclenché au clic");
assert(rows[1].classList.contains('pnc-active') && !rows[0].classList.contains('pnc-active'), "bascule : surbrillance déplacée sur le fonds");
rows[0].click();
assert(rows[0].classList.contains('pnc-active'), "bascule : retour à la vue portefeuille");
assert(q("k-start").textContent === before, "bascule : KPI restauré au retour portefeuille");

// ── Widget 4 — détail par contrat en accordéon ──
const w4 = document.querySelector('.nc-acc-tbl');
assert(w4 !== null, "détail par contrat : tableau accordéon présent");
const head = w4.textContent;
for (const col of ["Cap. engagé","Cap. appelé","Non appelé réel","Non appelé estimé","MOIC","Valeur (dern. constat.)"])
  assert(head.includes(col), `détail : colonne ${col}`);
assert(head.includes("TOTAL"), "détail : ligne TOTAL");
// D-UI-2 (31/07) : la colonne « Cible (MOIC/TRI) » est SUPPRIMÉE du tableau fonds — la cible
// vit dans le sous-texte du fonds. Chapeau adaptatif aux classes présentes.
assert(!head.includes("Cible (MOIC/TRI)"), "D-UI-2 : colonne Cible absente du tableau fonds");
assert([...w4.querySelectorAll('.cdet')].some(c=>/Cible\s/.test(c.textContent)), "D-UI-2 : la cible vit dans le sous-texte");
const hd4 = w4.closest('.cote-exh').querySelector('.cote-exh-hd');
assert(hd4 && /^Fonds (de |d'|non cotés)/.test(hd4.textContent), `D-UI-2 : chapeau adaptatif (« ${hd4 ? hd4.textContent : '∅'} »)`);
// L'accordéon dépliable n'existe qu'en mode « envoyee » : en « presentee » (défaut) le
// template neutralise volontairement le clic (reporting.mode — cf. performance_nc.html.j2).
// Le test s'adapte au rendu reçu et DIT dans quel mode il a jugé.
const acc0 = w4.querySelector('.acc-head.acc-clickable');
if (acc0) {
  const det0 = acc0.nextElementSibling;
  assert(det0.hidden === true, "détail [envoyee] : dépliant caché par défaut");
  acc0.click();
  assert(det0.hidden === false, "détail [envoyee] : dépliant ouvert au clic");
  assert(/Appel prévu/.test(det0.textContent) && /15\/09\/2026/.test(det0.textContent), "détail [envoyee] : échéancier prévisionnel (appel Altaroc 15/09/2026)");
  assert(/TVPI/.test(det0.textContent) && /DPI/.test(det0.textContent) && /TRI/.test(det0.textContent), "détail [envoyee] : stats TVPI/DPI/TRI dans le dépliant");
} else {
  assert(w4.querySelector('.acc-head') !== null, "détail [presentee] : lignes présentes (accordéon statique voulu)");
  assert(w4.querySelector('.acc-detail') === null, "détail [presentee] : aucun dépliant émis");
}

// glossaire + pitch commercial
const gloss = document.querySelector('.nc-acc-tbl') && document.querySelectorAll('.pnc-gloss');
assert([...document.querySelectorAll('.pnc-gloss')].some(g=>/TVPI/.test(g.textContent)&&/DPI/.test(g.textContent)&&/TRI/.test(g.textContent)), "glossaire TVPI/DPI/TRI présent");
assert(document.querySelector('.pnc-pitch') !== null, "pitch commercial rétabli avec la composition (30/07)");
assert(/fonds/.test(document.querySelector('.pnc-pitch').textContent), "pitch : contenu déterministe présent");

console.log(process.exitCode ? "\nÉCHECS" : "\nTOUT OK");
// Sortie explicite : les scripts décoratifs du rendu (animations) laissent des timers vivants
// sous jsdom — sans exit(), le process pend au lieu de rendre la main (constaté le 30/07).
process.exit(process.exitCode || 0);
