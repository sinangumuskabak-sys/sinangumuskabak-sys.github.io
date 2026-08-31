// LearnGuage — kucuk ilerletme katmani (vanilya JS, defer ile yuklenir).
// JS kapaliyken hicbir sey gizli degil: .js sinifi burada eklenir, CSS yalnizca
// .js varliginda icerik gizler. Toplam is: kelime demosu, acilma gozlemcisi,
// dil menusu dis-tik kapama, yasal sayfa icindekiler vurgulayici.

document.documentElement.classList.add('js');

// ---------------------------------------------------------------------------
// Kelime demosu: dokun -> popover -> Kaydet -> sayaç + flash kart
// ---------------------------------------------------------------------------
(() => {
    const card = document.querySelector('[data-demo]');
    if (!card) return;

    const pop = card.querySelector('#demo-pop');
    const popWord = pop.querySelector('.pop-word');
    const popAdd = pop.querySelector('.pop-add');
    const counter = card.querySelector('#demo-n');
    const flash = document.getElementById('flash-word');
    let openBtn = null;
    let saved = 0;

    function openPop(btn) {
        openBtn = btn;
        popWord.textContent = btn.dataset.word;
        popAdd.dataset.word = btn.dataset.word;
        btn.setAttribute('aria-expanded', 'true');
        pop.hidden = false;

        // Kart icine, kelimenin altina yerlestir; kenarlara tasirma
        const cardBox = card.getBoundingClientRect();
        const btnBox = btn.getBoundingClientRect();
        const left = Math.max(12, Math.min(btnBox.left - cardBox.left, cardBox.width - pop.offsetWidth - 12));
        let top = btnBox.bottom - cardBox.top + 8;
        if (top + pop.offsetHeight > cardBox.height - 8) {
            top = Math.max(8, btnBox.top - cardBox.top - pop.offsetHeight - 8);
        }
        pop.style.left = `${left}px`;
        pop.style.top = `${top}px`;
    }

    function closePop() {
        if (openBtn) openBtn.setAttribute('aria-expanded', 'false');
        pop.hidden = true;
        openBtn = null;
    }

    card.querySelectorAll('button.w').forEach((btn) => {
        btn.addEventListener('click', () => {
            if (openBtn === btn) {
                closePop();
                return;
            }
            if (openBtn) openBtn.setAttribute('aria-expanded', 'false');
            openPop(btn);
        });
    });

    popAdd.addEventListener('click', () => {
        const btn = openBtn;
        if (btn && !btn.classList.contains('saved')) {
            btn.classList.add('saved');
            saved += 1;
            counter.textContent = saved;
            flash.textContent = btn.dataset.word;
            // Sayac/kart degisimini hafif vurgula (reduced-motion'da CSS kapatir)
            flash.classList.remove('tick');
            void flash.offsetWidth;
            flash.classList.add('tick');
        }
        closePop();
        btn?.focus();
    });

    card.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !pop.hidden) {
            closePop();
            if (openBtn) openBtn.focus();
            else card.querySelector('button.w[aria-expanded="true"]')?.focus();
        }
    });

    // Kart disina tiklayinca kapat (yalnizca JS iyilestirmesi)
    document.addEventListener('pointerdown', (e) => {
        if (!pop.hidden && !card.contains(e.target)) closePop();
    });
})();

// ---------------------------------------------------------------------------
// Acilma gozlemcisi: yalnizca .js ile; bir kez oynar, geri saklamaz
// ---------------------------------------------------------------------------
// Ilke: bos bolum gostermek imkansiz olmali. Hareket sus; icerik kazanir.
(() => {
    const items = [...document.querySelectorAll('[data-reveal]')];
    if (!items.length) return;
    const reveal = (el) => el.classList.add('in');
    const revealAll = () => items.forEach(reveal);
    try {
        // Baslangicta gorunur alanda olan ya da ustunde kalan her sey aninda acilir
        const vh = window.innerHeight || document.documentElement.clientHeight;
        const pending = [];
        for (const el of items) {
            const r = el.getBoundingClientRect();
            if (r.top <= vh && r.bottom >= 0) reveal(el);
            else pending.push(el);
        }
        let io = null;
        if ('IntersectionObserver' in window && pending.length) {
            io = new IntersectionObserver(
                (entries) => {
                    for (const en of entries) {
                        if (!en.isIntersecting) continue;
                        reveal(en.target);
                        io.unobserve(en.target);
                    }
                },
                { rootMargin: '0px 0px 10% 0px', threshold: 0 },
            );
            pending.forEach((el) => io.observe(el));
        } else if (pending.length) {
            revealAll();
        }
        // Emniyet agi: ne olursa olsun icerik gorunur kalir
        const flush = () => {
            revealAll();
            io?.disconnect();
        };
        window.addEventListener('load', () => setTimeout(flush, 1500));
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') flush();
        });
        window.addEventListener('beforeprint', flush);
    } catch (e) {
        revealAll();
    }
})();

// ---------------------------------------------------------------------------
// Dil menusu: dis-tik kapama (details zaten Esc'yi yerel olarak desteklemez)
// ---------------------------------------------------------------------------
(() => {
    const menu = document.querySelector('[data-lang-menu]');
    if (!menu) return;
    document.addEventListener('pointerdown', (e) => {
        if (menu.open && !menu.contains(e.target)) menu.open = false;
    });
    menu.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && menu.open) {
            menu.open = false;
            menu.querySelector('summary').focus();
        }
    });
    // Dil secilince menu acik kalmamali (ayni sayfada kalan tek link)
    menu.querySelectorAll('a').forEach((a) =>
        a.addEventListener('click', () => {
            menu.open = false;
        }),
    );
})();

// ---------------------------------------------------------------------------
// Yasal sayfa icindekiler: okuma cizgisinin ustundeki son basligi vurgula.
// Dar bir kesisme bandi yerine "en ustteki gecen baslik" yontemi — basliklar
// iki geri cagri arasinda bandi atlamaz; --header-h tek dogru kaynaktadir.
// ---------------------------------------------------------------------------
(() => {
    const toc = document.querySelector('[data-toc]');
    const body = document.querySelector('[data-doc-body]');
    if (!toc || !body) return;
    const links = new Map([...toc.querySelectorAll('a')].map((a) => [a.hash.slice(1), a]));
    const heads = [...links.keys()].map((id) => document.getElementById(id)).filter(Boolean);
    if (!heads.length) return;
    const headerH = (() => {
        const v = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-h'));
        return Number.isFinite(v) ? v : 64;
    })();
    let ticking = false;
    const setActive = () => {
        ticking = false;
        const line = headerH + 24;
        let current = heads[0];
        for (const h of heads) {
            if (h.getBoundingClientRect().top <= line) current = h;
            else break;
        }
        links.forEach((a) => a.classList.remove('toc-here'));
        links.get(current.id)?.classList.add('toc-here');
    };
    const onScroll = () => {
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(setActive);
        }
    };
    document.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    setActive();
})();
