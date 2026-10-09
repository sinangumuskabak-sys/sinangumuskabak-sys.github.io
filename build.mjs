// LearnGuage site uretici — bagimliliksiz (yalniz Node yerlesikleri).
//
// Neden betik: 6 dil x 5 sayfa = 30 HTML. Altbilgiye tek bir link eklemek elle
// 30 dosya duzenlemek demek olurdu. Icerik content/<dil>.json'da, iskelet burada.
//
// Kullanim:  node build.mjs
//
// KRITIK: Ingilizce sayfalar KOKE yazilir. /privacy.html, /terms.html ve
// /delete-account.html adresleri uygulamanin icinde (D:\mobile\constants\legal.ts)
// ve Play Console'da sabit — dosya adlari degisemez, dil dizinleri bunlarin
// YANINA kurulur.

import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));
const cfg = JSON.parse(readFileSync(join(ROOT, 'site.config.json'), 'utf8'));

const locales = cfg.locales;
const content = Object.fromEntries(
    locales.map((l) => [l.code, JSON.parse(readFileSync(join(ROOT, 'content', `${l.code}.json`), 'utf8'))]),
);

/** Sayfa adindan o dildeki koke-mutlak yol. Ingilizce = kok. */
function pageUrl(localeCode, page) {
    const loc = locales.find((l) => l.code === localeCode);
    const prefix = loc.dir ? `/${loc.dir}` : '';
    return page === 'index' ? `${prefix}/` : `${prefix}/${page}.html`;
}

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/**
 * Metindeki yer tutucular tek kaynaktan (site.config.json) doldurulur.
 * {{url:sayfa}} O ANKI DILE gore cozulur — icerik dosyalarinda "/tr/privacy.html"
 * gibi elle yazilmis yollar olmasin (dil eklenince/dizin degisince sessizce kirilir).
 */
function fillRaw(text, localeCode = cfg.defaultLocale) {
    return String(text)
        .replace(/\{\{url:([a-z-]+)\}\}/g, (_, page) => {
            if (!cfg.pages.includes(page)) throw new Error(`Bilinmeyen sayfa yer tutucusu: {{url:${page}}}`);
            return pageUrl(localeCode, page);
        })
        .replaceAll('{{email}}', cfg.contactEmail)
        .replaceAll('{{emailLink}}', `<a href="mailto:${cfg.contactEmail}">${cfg.contactEmail}</a>`)
        .replaceAll('{{app}}', cfg.appName)
        .replaceAll('{{package}}', cfg.packageName)
        .replaceAll('{{playSubs}}', cfg.playSubscriptionsUrl)
        .replaceAll('{{play}}', cfg.playUrl);
}

/** Icerik bloklarini HTML'e cevirir. Blok tipleri: h2, h3, p, ul, ol, note */
function renderBlocks(blocks, localeCode) {
    return blocks
        .map((b) => {
            if (b.h2) return `<h2>${fillRaw(b.h2, localeCode)}</h2>`;
            if (b.h3) return `<h3>${fillRaw(b.h3, localeCode)}</h3>`;
            if (b.p) return `<p>${fillRaw(b.p, localeCode)}</p>`;
            if (b.note) return `<p class="note">${fillRaw(b.note, localeCode)}</p>`;
            if (b.ul) return `<ul>\n${b.ul.map((i) => `  <li>${fillRaw(i, localeCode)}</li>`).join('\n')}\n</ul>`;
            if (b.ol) return `<ol>\n${b.ol.map((i) => `  <li>${fillRaw(i, localeCode)}</li>`).join('\n')}\n</ol>`;
            throw new Error(`Bilinmeyen blok tipi (${localeCode}): ${JSON.stringify(b)}`);
        })
        .join('\n');
}

function langBar(localeCode, page) {
    const items = locales
        .map((l) =>
            l.code === localeCode
                ? `<span class="lang-current" aria-current="true">${esc(l.name)}</span>`
                : `<a href="${pageUrl(l.code, page)}" hreflang="${l.htmlLang}">${esc(l.name)}</a>`,
        )
        .join('');
    return `<nav class="langbar" aria-label="Language">${items}</nav>`;
}

function hreflangTags(page) {
    const alts = locales
        .map((l) => `<link rel="alternate" hreflang="${l.htmlLang}" href="${cfg.baseUrl}${pageUrl(l.code, page)}">`)
        .join('\n');
    return `${alts}\n<link rel="alternate" hreflang="x-default" href="${cfg.baseUrl}${pageUrl(cfg.defaultLocale, page)}">`;
}

function siteNav(localeCode, current, c) {
    const items = cfg.pages
        .map((p) => {
            const label = esc(c.nav[p]);
            return p === current
                ? `<span class="nav-current">${label}</span>`
                : `<a href="${pageUrl(localeCode, p)}">${label}</a>`;
        })
        .join('');
    return `<nav class="sitenav" aria-label="${esc(c.nav.label)}">${items}</nav>`;
}

function footer(localeCode, c) {
    const links = cfg.pages
        .filter((p) => p !== 'index')
        .map((p) => `<a href="${pageUrl(localeCode, p)}">${esc(c.nav[p])}</a>`)
        .join('');
    return `<footer class="site-footer">
  <p class="brand">${esc(cfg.appName)}</p>
  <nav aria-label="${esc(c.nav.label)}">${links}</nav>
  <p class="muted">${fillRaw(c.footer.contact, localeCode)}</p>
  <p class="muted small">${fillRaw(c.footer.copyright, localeCode)}</p>
</footer>`;
}

function shell({ localeCode, page, c, title, description, body, wide }) {
    const loc = locales.find((l) => l.code === localeCode);
    // Varliklar koke-mutlak: alt dizinlerdeki sayfalarda da ayni yol calisir.
    return `<!DOCTYPE html>
<html lang="${loc.htmlLang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<meta name="color-scheme" content="light dark">
<link rel="canonical" href="${cfg.baseUrl}${pageUrl(localeCode, page)}">
${hreflangTags(page)}
<link rel="icon" href="/assets/icon.png" type="image/png">
<link rel="stylesheet" href="/assets/site.css">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="${cfg.baseUrl}${pageUrl(localeCode, page)}">
<meta property="og:image" content="${cfg.baseUrl}/assets/icon.png">
</head>
<body>
<a class="skip" href="#main">${esc(c.nav.skip)}</a>
<header class="site-header">
  <a class="logo" href="${pageUrl(localeCode, 'index')}">
    <img src="/assets/icon.png" alt="" width="32" height="32">
    <span>${esc(cfg.appName)}</span>
  </a>
  ${siteNav(localeCode, page, c)}
  ${langBar(localeCode, page)}
</header>
<main id="main" class="${wide ? 'wide' : 'prose'}">
${body}
</main>
${footer(localeCode, c)}
</body>
</html>
`;
}

// ---------------------------------------------------------------------------
// Sayfalar
// ---------------------------------------------------------------------------

function renderHome(localeCode, c) {
    const h = c.home;
    const fill = (s) => fillRaw(s, localeCode); // bu sayfadaki tum metinler bu dile cozulur
    const features = h.features
        .map(
            (f) => `  <article class="feature">
    <h3>${esc(f.title)}</h3>
    <ul>
${f.items.map((i) => `      <li>${fill(i)}</li>`).join('\n')}
    </ul>
  </article>`,
        )
        .join('\n');

    const screens = cfg.screens
        .map((s, i) => {
            const cap = h.screens[s] ?? '';
            return `  <figure class="screen">
    <div class="phone"><img src="/assets/screens/${localeCode}/${s}.jpg" alt="${esc(cap)}" loading="lazy" width="270" height="480"></div>
    <figcaption>${esc(cap)}</figcaption>
  </figure>`;
        })
        .join('\n');

    const faq = h.faq
        .map(
            (q) => `  <details>
    <summary>${esc(q.q)}</summary>
    <div>${fill(q.a)}</div>
  </details>`,
        )
        .join('\n');

    return `<section class="hero">
  <h1>${esc(h.headline)}</h1>
  <p class="lede">${fill(h.subhead)}</p>
  <p class="cta"><a class="btn" href="${cfg.playUrl}">${esc(h.cta)}</a></p>
  <p class="muted small">${fill(h.ctaNote)}</p>
</section>

<section class="features">
  <h2>${esc(h.featuresTitle)}</h2>
  <div class="feature-grid">
${features}
  </div>
</section>

<section class="screens">
  <h2>${esc(h.screensTitle)}</h2>
  <div class="screen-row">
${screens}
  </div>
</section>

<section class="langs">
  <h2>${esc(h.languagesTitle)}</h2>
  <p>${fill(h.learnLanguages)}</p>
  <p>${fill(h.uiLanguages)}</p>
</section>

<section class="premium">
  <h2>${esc(h.premiumTitle)}</h2>
  <p>${fill(h.premiumBody)}</p>
  <ul>
${h.premiumItems.map((i) => `    <li>${fill(i)}</li>`).join('\n')}
  </ul>
  <p class="note">${fill(h.premiumPriceNote)}</p>
</section>

<section class="faq">
  <h2>${esc(h.faqTitle)}</h2>
${faq}
</section>`;
}

function renderDoc(localeCode, c, key) {
    const d = c[key];
    const notice = d.translationNotice
        ? `<p class="translation-notice">${fillRaw(d.translationNotice, localeCode)}</p>`
        : '';
    return `<h1>${esc(d.title)}</h1>
<p class="muted">${fillRaw(d.meta, localeCode)}</p>
${notice}
${renderBlocks(d.blocks, localeCode)}`;
}

// ---------------------------------------------------------------------------
// Uretim
// ---------------------------------------------------------------------------

const written = [];

function emit(relPath, html) {
    const full = join(ROOT, relPath);
    mkdirSync(dirname(full), { recursive: true });
    writeFileSync(full, html, 'utf8');
    written.push(relPath);
}

for (const loc of locales) {
    const c = content[loc.code];
    const base = loc.dir ? `${loc.dir}/` : '';

    emit(
        `${base}index.html`,
        shell({
            localeCode: loc.code,
            page: 'index',
            c,
            title: c.meta.homeTitle,
            description: c.meta.homeDescription,
            body: renderHome(loc.code, c),
            wide: true,
        }),
    );

    for (const [page, key] of [
        ['privacy', 'privacy'],
        ['terms', 'terms'],
        ['delete-account', 'deleteAccount'],
        ['support', 'support'],
        ['about', 'about'],
    ]) {
        emit(
            `${base}${page}.html`,
            shell({
                localeCode: loc.code,
                page,
                c,
                title: `${c[key].title} — ${cfg.appName}`,
                description: c.meta[`${key}Description`] ?? c.meta.homeDescription,
                body: renderDoc(loc.code, c, key),
            }),
        );
    }
}

// 404: varsayilan dilde, dil secenekleriyle
{
    const c = content[cfg.defaultLocale];
    const links = locales
        .map((l) => `<a href="${pageUrl(l.code, 'index')}">${esc(l.name)}</a>`)
        .join('');
    emit(
        '404.html',
        shell({
            localeCode: cfg.defaultLocale,
            page: 'index',
            c,
            title: `404 — ${cfg.appName}`,
            description: c.notFound.title,
            body: `<h1>${esc(c.notFound.title)}</h1>\n<p>${fillRaw(c.notFound.body, cfg.defaultLocale)}</p>\n<nav class="langbar wrap">${links}</nav>`,
        }),
    );
}

// ---------------------------------------------------------------------------
// Kirik ic link kontrolu — 30 sayfayi elle gezmek gercekci degil
// ---------------------------------------------------------------------------

function allFiles(dir, acc = []) {
    for (const name of readdirSync(dir)) {
        if (name === '.git' || name === 'node_modules' || name === 'templates' || name === 'content') continue;
        const p = join(dir, name);
        if (statSync(p).isDirectory()) allFiles(p, acc);
        else acc.push(p);
    }
    return acc;
}

let broken = 0;
const htmlFiles = allFiles(ROOT).filter((f) => f.endsWith('.html'));
for (const file of htmlFiles) {
    const html = readFileSync(file, 'utf8');
    const hrefs = [...html.matchAll(/(?:href|src)="([^"]+)"/g)].map((m) => m[1]);
    for (const href of hrefs) {
        if (!href.startsWith('/')) continue; // dis baglantilar ve capa/mailto atlanir
        // Ekran gorselleri ayri kontrolde raporlanir; henuz eklenmemis olmalari
        // uretimi durdurmaz (duzen onlarsiz da bozulmuyor).
        if (href.startsWith('/assets/screens/')) continue;
        const target = href.endsWith('/') ? `${href}index.html` : href;
        const onDisk = join(ROOT, target);
        if (!existsSync(onDisk)) {
            console.error(`KIRIK LINK  ${file.replace(ROOT, '.')}  ->  ${href}`);
            broken++;
        }
    }
}

// Uygulamanin ve Play Console'un bagli oldugu adresler kokte duruyor mu
const critical = ['privacy.html', 'terms.html', 'delete-account.html'];
let missingCritical = 0;
for (const f of critical) {
    if (!existsSync(join(ROOT, f))) {
        console.error(`KRITIK ADRES EKSIK: /${f} (constants/legal.ts ve Play Console buraya bakiyor)`);
        missingCritical++;
    }
}

console.log(`${written.length} sayfa uretildi (${locales.length} dil x ${cfg.pages.length} sayfa + 404).`);
// Gorseller dil basina: assets/screens/<dil>/<ekran>.jpg
const missingScreens = locales.flatMap((l) => cfg.screens.filter((s) => !existsSync(join(ROOT, 'assets', 'screens', l.code, `${s}.jpg`))).map((s) => `${l.code}/${s}`));
if (missingScreens.length) {
    console.log(`Eksik ekran gorseli (duzen bozulmaz, sonra eklenebilir): ${missingScreens.join(', ')}`);
}
if (broken || missingCritical) {
    console.error(`\nBASARISIZ: ${broken} kirik link, ${missingCritical} eksik kritik adres.`);
    process.exit(1);
}
console.log('Kirik ic link yok. Kritik adresler yerinde.');
