# -*- coding: utf-8 -*-
"""
Ekran goruntulerindeki Turkce arayuz yazilarini hedef dile cevirir.

Yontem (goz karari YOK):
 1) Yaklasik arama kutusunda "zeminden farkli" pikseller taranip yazinin siki
    sinir kutusu bulunur.
 2) Punto, ORIJINAL Turkce dizeyle kalibre edilir (ayni yuksekligi veren boyut).
 3) Yazi rengi kutu icinde zeminden en cok ayrilan pikselden ornekenir.
 4) Kutu zeminle doldurulup ceviri ayni sol kenar + ayni taban cizgisine yazilir.

Metinler uygulamanin kendi ceviri dosyasindan (context/AppLanguageContext.tsx)
alinmistir — uydurma ceviri yoktur. Icerik (kitap metni, altyazi, transkript,
kelime karti sozcugu, sayilar, yuzde) HIC degistirilmez.

Kullanim:  python tools/localize-screens.py <dil>      (dil: tr en es pt fr de)
"""
from PIL import Image, ImageDraw, ImageFont
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
F = {w: os.path.join(FONTS, n) for w, n in
     {"r": "Roboto_400Regular.ttf", "m": "Roboto_500Medium.ttf", "b": "Roboto_700Bold.ttf"}.items()}

SRCDIR = r"C:\Users\sinan\Desktop\uygulama resimleri"
SHOT = {
    "home":       "Screenshot_2026-07-27-10-01-51-90_24215c64153c7310feb1903f457bc010.jpg",
    "reading":    "Screenshot_2026-07-27-10-02-39-01_24215c64153c7310feb1903f457bc010.jpg",
    "listening":  "Screenshot_2026-07-27-10-04-03-58_24215c64153c7310feb1903f457bc010.jpg",
    "vocabulary": "Screenshot_2026-07-27-10-05-20-06_24215c64153c7310feb1903f457bc010.jpg",
    "grammar":    "Screenshot_2026-07-27-10-05-03-49_24215c64153c7310feb1903f457bc010.jpg",
}

# --- bolge haritalari -------------------------------------------------------
# box: arama kutusu | w: agirlik | a: hizalama (l/c) | tr: orijinal Turkce
# bgp: zemin ornekleme noktasi | size: punto zorlamasi | wrap: satir sarma genisligi
SPEC = {
 "home": {
  "ad":              dict(box=(220,220,700,280),  w="m", a="l", tr="sinangumuskabak"),
  "takip_et":        dict(box=(135,420,700,485),  w="b", a="l", tr="İlerlemeni Takip Et"),
  "genel_yetkinlik": dict(box=(530,700,1010,750), w="m", a="l", tr="GENEL YETKİNLİK"),
  "seviyesi":        dict(box=(530,775,1010,845), w="b", a="l", tr="A2 Seviyesi"),
  "seviye_kucuk":    dict(box=(243,803,366,847),  w="r", a="l", tr="SEVİYE", size=34),
  "calisma_mod":     dict(box=(55,1095,700,1160), w="b", a="l", tr="Çalışma Modülleri"),
  "okuma":           dict(box=(100,1450,500,1505),w="b", a="l", tr="Okuma"),
  "okuma_alt":       dict(box=(100,1530,500,1585),w="r", a="l", tr="25 Kitap"),
  "dinleme":         dict(box=(600,1450,1005,1505),w="b",a="l", tr="Dinleme"),
  "dinleme_alt":     dict(box=(600,1530,1005,1585),w="r",a="l", tr="17 İçerik"),
  "dilbilgisi":      dict(box=(100,1910,500,1970),w="b", a="l", tr="Dil Bilgisi"),
  "dilbilgisi_alt":  dict(box=(100,1990,500,2045),w="r", a="l", tr="7 Çalışma"),
  "kelime":          dict(box=(600,1910,1005,1970),w="b",a="l", tr="Kelime"),
  "kelime_alt":      dict(box=(600,1990,1005,2045),w="r",a="l", tr="19 Yeni Kelime"),
  "tab_ana":         dict(box=(45,2212,230,2258), w="m", a="c", tr="Ana Sayfa",  bgp=(45,2260)),
  "tab_kitaplik":    dict(box=(300,2212,500,2258),w="m", a="c", tr="Kitaplık",   bgp=(300,2260)),
  "tab_kelimeler":   dict(box=(560,2212,790,2258),w="m", a="c", tr="Kelimeler",  bgp=(560,2260)),
  "tab_profil":      dict(box=(850,2212,1040,2258),w="m",a="c", tr="Profil",     bgp=(850,2260)),
 },
 "vocabulary": {
  "mod":       dict(box=(400,135,700,182),   w="m", a="c", tr="EZBER MODU"),
  "baslik":    dict(box=(350,188,740,240),   w="b", a="c", tr="Kelime Kartları"),
  "kaydir":    dict(box=(140,400,950,455),   w="r", a="c", tr="Bilmiyorsan Sola, Biliyorsan Sağa Kaydır"),
  # dokunma ikonu ~x315'te: arama kutusu 335'ten baslatildi, yoksa ikon yaziya
  # dahil olup merkezi sola kaydiriyor ve ceviri ikonun ustune biniyordu
  "dokun":     dict(box=(335,1715,860,1775), w="r", a="c", tr="Çeviriyi görmek için dokun"),
  "bilmiyorum":dict(box=(110,2120,530,2190), w="m", a="c", tr="Bilmiyorum"),
  "biliyorum": dict(box=(600,2120,1010,2190),w="m", a="c", tr="Biliyorum"),
 },
 "grammar": {
  "baslik":    dict(box=(140,168,760,235),   w="b", a="l", tr="Gramer Alıştırması"),
  "ilerleme":  dict(box=(55,318,420,378),    w="m", a="l", tr="Ders İlerlemesi"),
  # Cok satirli, ortalanmis cumle ipucu: sarmali cizim
  "ipucu_cumle": dict(box=(120,545,960,770), w="b", a="c", tr=">> Kesmeye devam eden kişi",
                      size=54, wrap=880),
  "surukle":   dict(box=(140,1078,950,1140), w="r", a="c", tr="Kelimeleri buraya sürükleyin veya dokunun"),
  "uzunbas":   dict(box=(80,1352,930,1412),  w="r", a="c", tr="i Kelimelerin çevirisi için üzerlerine uzun basılı tutun"),
  "kontrol":   dict(box=(55,2150,270,2220),  w="m", a="c", tr="Kontrol"),
  "sil":       dict(box=(330,2150,520,2220), w="m", a="c", tr="Sil"),
  "ipucu":     dict(box=(570,2150,770,2220), w="m", a="c", tr="İpucu"),
  "atla":      dict(box=(840,2150,1030,2220),w="m", a="c", tr="Atla"),
 },
 # Okuma/dinlemede butonlarin KENDI zemin renkleri var; zemin noktasi acikca
 # verilmezse tespit yaziyi degil butonu buluyor. Olculen renkler:
 # balon (250,243,225) | acik buton (228,211,181) | kahverengi buton (162,102,42)
 "reading": {
  "balon":     dict(box=(258,728,560,788),   w="b", a="l", tr="duydu",             bgp=(258,712)),
  "gostermore":dict(box=(375,850,700,900),   w="m", a="c", tr="Daha fazla göster", bgp=(300,845)),
  # "+" ikonu da siliniyor: yarim kalan ikon kirintisi birakmaktansa yaziyi
  # butona ortalamak daha temiz duruyor
  "ezbere":    dict(box=(350,955,715,1015),  w="m", a="c", tr="Ezbere Ekle",       bgp=(330,948)),
  "onceki":    dict(box=(165,2145,332,2202), w="m", a="c", tr="Önceki",            bgp=(200,2125)),
  "sonraki":   dict(box=(735,2145,900,2202), w="m", a="c", tr="Sonraki",           bgp=(800,2125)),
 },
 "listening": {
  "duraklat":  dict(box=(350,950,505,1010),  w="m", a="c", tr="Duraklat",          bgp=(320,942)),
  "balon":     dict(box=(408,1580,600,1645), w="b", a="l", tr="görülen",           bgp=(400,1565)),
  "gostermore":dict(box=(515,1705,810,1762), w="m", a="c", tr="Daha fazla göster", bgp=(470,1698)),
  "ezbere":    dict(box=(600,1812,845,1872), w="m", a="c", tr="Ezbere Ekle",       bgp=(560,1806)),
 },
}

# --- ceviriler --------------------------------------------------------------
# Arayuz dizeleri AppLanguageContext.tsx'ten; balon/ipucu metinleri o dildeki
# dogru karsiliklari (icerik cevirisi, uydurma degil).
TXT = {
 "home": {
  "ad": dict(tr="Kullanıcı", en="User", es="Usuario", pt="Usuário", fr="Utilisateur", de="Benutzer"),
  "takip_et": dict(tr="İlerlemeni Takip Et", en="Track Your Progress", es="Sigue Tu Progreso",
                   pt="Acompanhe Seu Progresso", fr="Suis Ta Progression", de="Verfolge Deinen Fortschritt"),
  "genel_yetkinlik": dict(tr="GENEL YETKİNLİK", en="OVERALL COMPETENCY", es="COMPETENCIA GENERAL",
                          pt="COMPETÊNCIA GERAL", fr="COMPÉTENCE GLOBALE", de="ALLGEMEINE KOMPETENZ"),
  "seviyesi": dict(tr="A2 Seviyesi", en="A2 Level", es="Nivel A2", pt="Nível A2", fr="Niveau A2", de="A2 Stufe"),
  "seviye_kucuk": dict(tr="SEVİYE", en="LEVEL", es="NIVEL", pt="NÍVEL", fr="NIVEAU", de="STUFE"),
  "calisma_mod": dict(tr="Çalışma Modülleri", en="Study Modules", es="Módulos de Estudio",
                      pt="Módulos de Estudo", fr="Modules d'étude", de="Lernmodule"),
  "okuma": dict(tr="Okuma", en="Reading", es="Lectura", pt="Leitura", fr="Lecture", de="Lesen"),
  "okuma_alt": dict(tr="25 Kitap", en="25 Books", es="25 Libros", pt="25 Livros", fr="25 Livres", de="25 Bücher"),
  "dinleme": dict(tr="Dinleme", en="Listening", es="Escucha", pt="Escuta", fr="Écoute", de="Hören"),
  "dinleme_alt": dict(tr="17 İçerik", en="17 Contents", es="17 Contenidos", pt="17 Conteúdos",
                      fr="17 Contenus", de="17 Inhalte"),
  "dilbilgisi": dict(tr="Dil Bilgisi", en="Grammar", es="Gramática", pt="Gramática", fr="Grammaire", de="Grammatik"),
  "dilbilgisi_alt": dict(tr="7 Çalışma", en="7 Exercises", es="7 Ejercicios", pt="7 Exercícios",
                         fr="7 Exercices", de="7 Übungen"),
  "kelime": dict(tr="Kelime", en="Vocabulary", es="Vocabulario", pt="Vocabulário", fr="Vocabulaire", de="Wortschatz"),
  "kelime_alt": dict(tr="19 Yeni Kelime", en="19 New Words", es="19 Palabras Nuevas",
                     pt="19 Palavras Novas", fr="19 Nouveaux Mots", de="19 Neue Wörter"),
  "tab_ana": dict(tr="Ana Sayfa", en="Home", es="Inicio", pt="Início", fr="Accueil", de="Startseite"),
  "tab_kitaplik": dict(tr="Kitaplık", en="Library", es="Biblioteca", pt="Biblioteca", fr="Bibliothèque", de="Bibliothek"),
  "tab_kelimeler": dict(tr="Kelimeler", en="Words", es="Palabras", pt="Palavras", fr="Mots", de="Wörter"),
  "tab_profil": dict(tr="Profil", en="Profile", es="Perfil", pt="Perfil", fr="Profil", de="Profil"),
 },
 "vocabulary": {
  "mod": dict(tr="EZBER MODU", en="MEMORIZATION MODE", es="MODO MEMORIZACIÓN",
              pt="MODO DE MEMORIZAÇÃO", fr="MODE MÉMORISATION", de="MERKMODUS"),
  "baslik": dict(tr="Kelime Kartları", en="Word Cards", es="Tarjetas de Palabras",
                 pt="Cartões de Palavras", fr="Cartes de Mots", de="Wortkarten"),
  "kaydir": dict(tr="Bilmiyorsan Sola, Biliyorsan Sağa Kaydır", en="Swipe Left if you do not know, Right if you know",
                 es="Desliza a la izquierda si no sabes, a la derecha si sabes",
                 pt="Deslize para a esquerda se não souber, para a direita se souber",
                 fr="Glissez à gauche si vous ne savez pas, à droite si vous savez",
                 de="Nach links wischen, wenn du es nicht weißt, nach rechts, wenn du es weißt"),
  "dokun": dict(tr="Çeviriyi görmek için dokun", en="Tap to see translation", es="Toca para ver la traducción",
                pt="Toque para ver a tradução", fr="Appuyez pour voir la traduction",
                de="Tippen, um die Übersetzung zu sehen"),
  "bilmiyorum": dict(tr="Bilmiyorum", en="I Don't Know", es="No Sé", pt="Não Sei",
                     fr="Je Ne Sais Pas", de="Weiß Ich Nicht"),
  "biliyorum": dict(tr="Biliyorum", en="I Know", es="Sé", pt="Sei", fr="Je Sais", de="Weiß Ich"),
 },
 "grammar": {
  "baslik": dict(tr="Gramer Alıştırması", en="Grammar Exercise", es="Ejercicio de Gramática",
                 pt="Exercício de Gramática", fr="Exercice de Grammaire", de="Grammatikübung"),
  "ilerleme": dict(tr="Ders İlerlemesi", en="Lesson Progress", es="Progreso de la Lección",
                   pt="Progresso da Lição", fr="Progression de la Leçon", de="Lektionsfortschritt"),
  # Alistirmanin ipucu cumlesi: "He's the one who keeps cutting the >>" ifadesinin
  # kullanicinin ana dilindeki karsiligi (icerik cevirisi)
  "ipucu_cumle": dict(tr=">> Kesmeye devam eden kişi", en=">> The one who keeps cutting",
                      es=">> El que sigue cortando", pt=">> Aquele que continua cortando",
                      fr=">> Celui qui continue à couper", de=">> Derjenige, der weiter schneidet"),
  "surukle": dict(tr="Kelimeleri buraya sürükleyin veya dokunun", en="Drag words here or tap them",
                  es="Arrastra las palabras aquí o tócalas", pt="Arraste as palavras aqui ou toque nelas",
                  fr="Faites glisser les mots ici ou appuyez dessus",
                  de="Ziehe Wörter hierher oder tippe sie an"),
  "uzunbas": dict(tr="i Kelimelerin çevirisi için üzerlerine uzun basılı tutun",
                  en="i Long press words to see translations",
                  es="i Mantén presionadas las palabras para ver traducciones",
                  pt="i Pressione longamente as palavras para ver traduções",
                  fr="i Appuyez longuement sur les mots pour voir les traductions",
                  de="i Lange auf Wörter drücken, um Übersetzungen zu sehen"),
  "kontrol": dict(tr="Kontrol", en="Check", es="Comprobar", pt="Verificar", fr="Vérifier", de="Prüfen"),
  "sil": dict(tr="Sil", en="Delete", es="Eliminar", pt="Excluir", fr="Supprimer", de="Löschen"),
  "ipucu": dict(tr="İpucu", en="Hint", es="Pista", pt="Dica", fr="Indice", de="Hinweis"),
  "atla": dict(tr="Atla", en="Skip", es="Omitir", pt="Pular", fr="Passer", de="Überspringen"),
 },
 "reading": {
  "onceki": dict(tr="Önceki", en="Previous", es="Anterior", pt="Anterior", fr="Précédent", de="Zurück"),
  "sonraki": dict(tr="Sonraki", en="Next", es="Siguiente", pt="Próximo", fr="Suivant", de="Weiter"),
  "gostermore": dict(tr="Daha fazla göster", en="Show more", es="Mostrar más", pt="Mostrar mais",
                     fr="Afficher plus", de="Mehr anzeigen"),
  "ezbere": dict(tr="Ezbere Ekle", en="Add to Memorize", es="Añadir a Memorizar",
                 pt="Adicionar para Memorizar", fr="Ajouter à Mémoriser", de="Zum Merken Hinzufügen"),
  # "heard" sozcugunun o dildeki karsiligi (icerik cevirisi)
  "balon": dict(tr="duydu", en="heard", es="oyó", pt="ouviu", fr="entendu", de="hörte"),
 },
 "listening": {
  "duraklat": dict(tr="Duraklat", en="Pause", es="Pausar", pt="Pausar", fr="Pause", de="Pause"),
  "gostermore": dict(tr="Daha fazla göster", en="Show more", es="Mostrar más", pt="Mostrar mais",
                     fr="Afficher plus", de="Mehr anzeigen"),
  "ezbere": dict(tr="Ezbere Ekle", en="Add to Memorize", es="Añadir a Memorizar",
                 pt="Adicionar para Memorizar", fr="Ajouter à Mémoriser", de="Zum Merken Hinzufügen"),
  # "seen" sozcugunun karsiligi
  "balon": dict(tr="görülen", en="seen", es="visto", pt="visto", fr="vu", de="gesehen"),
 },
}

CROP_TOP, CROP_BOTTOM, OUT_W = 108, 2258, 540


def run(lang, outdir):
    os.makedirs(outdir, exist_ok=True)
    for screen, fname in SHOT.items():
        im = Image.open(os.path.join(SRCDIR, fname)).convert("RGB")
        px, draw = im.load(), ImageDraw.Draw(im)

        def tight(box, bg, tol=28):
            x0, y0, x1, y1 = box
            mnx = mny = mxx = mxy = None
            for y in range(y0, y1):
                for x in range(x0, x1):
                    r, g, b = px[x, y]
                    if abs(r-bg[0])+abs(g-bg[1])+abs(b-bg[2]) > tol:
                        mnx = x if mnx is None or x < mnx else mnx
                        mxx = x if mxx is None or x > mxx else mxx
                        mny = y if mny is None or y < mny else mny
                        mxy = y if mxy is None or y > mxy else mxy
            return None if mnx is None else (mnx, mny, mxx+1, mxy+1)

        def tcolor(bb, bg):
            best, bd = None, -1
            for y in range(bb[1], bb[3]):
                for x in range(bb[0], bb[2]):
                    c = px[x, y]
                    d = abs(c[0]-bg[0])+abs(c[1]-bg[1])+abs(c[2]-bg[2])
                    if d > bd: bd, best = d, c
            return best

        def fit(path, text, h):
            best, bd = 12, 1e9
            for s in range(12, 96):
                bb = ImageFont.truetype(path, s).getbbox(text)
                d = abs((bb[3]-bb[1]) - h)
                if d < bd: bd, best = d, s
            return best

        for key, s in SPEC[screen].items():
            new = TXT[screen][key][lang]
            if new == s["tr"]:
                continue                      # Turkce set: degisiklik yok
            box = s["box"]
            bg = px[s["bgp"][0], s["bgp"][1]] if "bgp" in s else px[box[0]+2, box[1]+2]
            bb = tight(box, bg)
            if bb is None:
                print(f"  ! {screen}/{key}: yazi bulunamadi"); continue
            col = tcolor(bb, bg)
            size = s.get("size") or fit(F[s["w"]], s["tr"], bb[3]-bb[1])
            font = ImageFont.truetype(F[s["w"]], size)
            if "wrap" in s:
                # Cok satirli ortalanmis blok: kelime kelime sar, dikeyde ortala
                words, lines, cur = new.split(), [], ""
                for wd in words:
                    t = (cur + " " + wd).strip()
                    if font.getbbox(t)[2] - font.getbbox(t)[0] <= s["wrap"] or not cur:
                        cur = t
                    else:
                        lines.append(cur); cur = wd
                if cur: lines.append(cur)
                draw.rectangle((bb[0]-6, bb[1]-6, bb[2]+6, bb[3]+6), fill=bg)
                lh = int(size * 1.35)
                cx, cy = (bb[0]+bb[2])//2, (bb[1]+bb[3])//2
                y = cy - (len(lines)*lh)//2
                for ln in lines:
                    nb = font.getbbox(ln)
                    draw.text((cx-(nb[2]-nb[0])//2-nb[0], y), ln, font=font, fill=col)
                    y += lh
                print(f"  {screen}/{key}: {len(lines)} satir")
                continue

            # cok uzun ceviriler kutuya sigmiyorsa puntoyu kademeli kucult
            avail = box[2] - box[0]
            while size > 12 and (font.getbbox(new)[2] - font.getbbox(new)[0]) > avail:
                size -= 1
                font = ImageFont.truetype(F[s["w"]], size)
            rb = font.getbbox(s["tr"])
            draw.rectangle((bb[0]-3, bb[1]-3, bb[2]+3, bb[3]+3), fill=bg)
            if s["a"] == "l":
                draw.text((bb[0]-rb[0], bb[1]-rb[1]), new, font=font, fill=col)
            else:
                cx = (bb[0]+bb[2])//2
                nb = font.getbbox(new)
                draw.text((cx-(nb[2]-nb[0])//2-nb[0], bb[1]-rb[1]), new, font=font, fill=col)

        im = im.crop((0, CROP_TOP, im.width, CROP_BOTTOM))
        h = round(im.height * OUT_W / im.width)
        im = im.resize((OUT_W, h), Image.LANCZOS)
        out = os.path.join(outdir, f"{screen}.jpg")
        im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
        print(f"  {lang}/{screen}.jpg  {os.path.getsize(out)//1024} KB")


if __name__ == "__main__":
    lang = sys.argv[1]
    run(lang, os.path.join(HERE, "..", "assets", "screens", lang))
