# 🃏 Açık Arttırma — Kart Tasarım Rehberi & Master Prompt Şablonu

Bu doküman, "Açık Arttırma" oyunundaki tüm gizli aksiyon kartlarının görsel bütünlüğünü, retro 32-bit pixel art sanat tarzını ve tipografisini kalıcı olarak korumak için hazırlanmıştır. Gelecekte eklenecek tüm kartlar bu şablona göre üretilecektir.

---

## 🎨 Tasarım Dili & Görsel Kurallar

1. **Format & En-Boy Oranı:**
   - 2:3 Dikey Koleksiyon Kartı Formatı (800x1200 px / 1696x2528 px).
2. **Çerçeve (Frame):**
   - Koyu obsidiyen/gece mavisi kadife zemin üzerinde **Antik Barok Altın Varaklı Çerçeve** (Ornate Antique Gold Filigree Frame).
   - Köşelerde kabartmalı altın oymalar ve metalik parlama efektleri.
3. **Üst Başlık (Card Title):**
   - Kartın en üstünde, altın kemer/parşömen içinde kalın, temiz altın yaldızlı Türkçe kart adı (Örn: **MÜHÜR**, **BAHŞİŞ**, **KALKAN**).
4. **Merkez İllüstrasyon (Center Artwork - ZORUNLU 32-BIT PIXEL ART):**
   - Kartın tam ortasında, zengin renk paletine sahip, net hatlı, canlı gölgelendirmeli **32-Bit Retro Pixel Art** oyun ikonu.
   - Pikseller net ve belirgin olmalı; yumuşak vektör veya 3D render olmamalıdır.
5. **Alt Açıklama Plaketi (Description Box):**
   - Kartın alt 1/4'lük kısmında altın bordürlü koyu şık bir açıklama kutusu.
   - İçerisinde kartın Türkçe oyun etkisi okunaklı, temiz bir şekilde yazılı olmalıdır.

---

## 🔮 Master Prompt Şablonu (Gelecek Kartlar İçin)

```text
Generate a vertical fantasy trading card (2:3 aspect ratio, 800x1200) for the strategy auction game "Açık Arttırma".

CARD NAME: "{CARD_NAME}"
CARD CATEGORY: "{CARD_CATEGORY}" (Ödül & Gelir / Ceza & Saldırı / Savunma & Taktik / Ağır Lanet)
DESCRIPTION TEXT: "{CARD_DESCRIPTION}"

CRITICAL VISUAL COMPOSITION:
1. OUTER FRAME: Elaborate antique baroque gold filigree frame with ornate sculpted golden corners and delicate gold leaf embellishments on a deep obsidian black background.
2. TOP TITLE BANNER: An ornate embossed golden arch banner at the top displaying the exact bold title "{CARD_NAME}" in sharp, metallic golden uppercase lettering.
3. CENTERPIECE (STRICT 32-BIT RETRO PIXEL ART):
   - A bold, beautifully shaded 32-bit pixel art illustration depicting {ART_DESCRIPTION}.
   - Authentic retro game pixel cluster shading, vivid color palette, glowing pixel spark particles, sharp pixel silhouette (NOT smooth 3D, NOT vector art, true high-quality pixel art).
4. BOTTOM DESCRIPTION PLAQUE:
   - A dark semi-translucent ornate plaque with thin gold border filigree at the bottom of the card.
   - Containing the clear card description: "{CARD_DESCRIPTION}".
```

---

## 📋 15 Kartlık Tam Liste & Özellikleri

| # | Kart Adı | Kategori | Mağaza Bedeli | Bekleme | Hedef | Merkez Pixel Art Görseli | Kart Üzerindeki Açıklama |
|---|---|---|---|---|---|---|---|
| 1 | **BAHŞİŞ** | 💰 Ödül & Gelir | 140 P | 2 Tur | Kendine | Parıldayan altın piksel madeni para / sikke | "Kasana anında +1 ₺ nakit bütçe ekler." |
| 2 | **PİYANGO** | 💰 Ödül & Gelir | 250 P | 2 Tur | Kendine | Renkli dönen karnaval piksel şans çarkı | "Kasana anında 1-4 ₺ arası nakit bütçe ekler." |
| 3 | **YATIRIM** | 💰 Ödül & Gelir | 220 P | 3 Tur | Kendine | Ağzına kadar altın dolu ikiz çuval | "Kasana anında +2 ₺ nakit bütçe ekler." |
| 4 | **SERMAYE** | 💰 Ödül & Gelir | 320 P | 3 Tur | Kendine | Üst üste dizili 3 adet parlayan altın külçesi | "Kasana anında +3 ₺ nakit bütçe ekler." |
| 5 | **KARA PARA** | 💰 Ödül & Gelir | 420 P | 4 Tur | Kendine | Zümrüt yeşili parlayan gizemli kara para çantası | "Kasana anında +4 ₺ nakit bütçe ekler." |
| 6 | **TEBLİGAT** | ⚔️ Ceza & Saldırı | 180 P | 2 Tur | Rakip | Kırmızı mühürlü mahkeme parşömeni ve tokmak | "Seçilen rakibin kasasından anında 1 ₺ siler." |
| 7 | **HACİZ** | ⚔️ Ceza & Saldırı | 260 P | 3 Tur | Rakip | Kırmızı zincirlenmiş ev ve HACİZ damgası | "Seçilen rakibin kasasından anında 2 ₺ siler." |
| 8 | **İFLAS** | ⚔️ Ceza & Saldırı | 380 P | 4 Tur | Rakip | Kırık kilitli, zincirlere sarılı çelik kasa | "Seçilen rakibin kasasından anında 3 ₺ siler." |
| 9 | **HARAÇ** | ⚔️ Ceza & Saldırı | 400 P | 4 Tur | Tüm Masa | Paraları kendine çeken altın at nalı / mıknatıs | "Masadaki her oyuncudan 1 ₺ çalar ve kasana ekler." |
| 10 | **KALKAN** | 🛡️ Savunma & Taktik | 240 P | 3 Tur | Kendine | Mavi parıldayan şövalye kalkanı ve koruma aurası | "Sana oynanan bir saldırı veya ceza kartını engeller." |
| 11 | **VETO** | 🛡️ Savunma & Taktik | 250 P | 3 Tur | Tüm Masa | Masaya inen ve şok dalgası yayan altın müzayede tokmağı | "Çıkan ürün iptal edilir ve şerit tekrar döndürülür." |
| 12 | **DONDURMA** | 🛡️ Savunma & Taktik | 180 P | 2 Tur | Rakip | Buz kristalleriyle kaplı parlayan donmuş mızrak | "Seçtiğin 1 oyuncu bu tur teklif veremez." |
| 13 | **KAYIP SLOT** | 💀 Ağır Lanet | 400 P | 4 Tur | Rakip | Kilitli karanlık sandık ve kırmızı X işareti | "Hedef oyuncunun maksimum kadro kapasitesini 1 azaltır." |
| 14 | **KARA LANET** | 💀 Ağır Lanet | 400 P | 4 Tur | Rakip | Boynuzlu, gözlerinden alev çıkan mor iblis kurukafası | "Kadrosunu doldurana kadar boş geçen her tur 1 ₺ silinir." |
| 15 | **MÜHÜR** | 💀 Ağır Lanet | 340 P | 3 Tur | Rakip | Kilit mühürlü ve altın zincirlerle kilitli kart destesi | "Seçilen rakibin elini 2 tur kilitler; hiçbir gizli kart kullanamaz." |
