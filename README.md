---
license: cc-by-4.0
language:
  - tr
task_categories:
  - text-classification
  - token-classification
tags:
  - turkish
  - retail
  - merchandising
  - intent-classification
  - slot-filling
  - synthetic
pretty_name: "merch-tr-intent: Türkçe perakende merchandising soru → intent + slot"
size_categories:
  - 1K<n<10K
---

# merch-tr-intent

Türkçe **perakende merchandising / planlama** sorularını yapılandırılmış sorguya çeviren asistanlar için
intent sınıflandırma ve slot çıkarma veri seti. Örnek:

```json
{"text": "erkek triko geçen hafta kaç sattı", "intent": "satis",
 "slots": {"cinsiyet": "ERKEK", "urun_grubu": "TRIKO", "donem": "GECEN_HAFTA"}}
```

Amaç: "chino bu hafta kaç sattı, cover kaç?" gibi günlük soruları bir dil modeline SQL yazdırmadan, önceden
tanımlı sorgu şablonlarına yönlendirmek. Model yalnız **hangi soru tipi** ve **hangi parametreler** kararını verir;
rakamı veri kaynağı hesaplar. Bu tasarım yanlış sayı üretme riskini sıfırlar.

## İçerik

| Bölme | Kayıt | Not |
|---|---|---|
| train | ~2.090 | 18 intent |
| test | ~520 | **şablon düzeyinde ayrık**: test şablonları eğitimde hiç görülmez |

Her kayıt: `id`, `text`, `intent`, `slots` (sözlük; boş olabilir).

### Intent'ler (18)

| intent | Soru tipi |
|---|---|
| satis | satış ciro/adet |
| buyume | geçen yıl / plan / bütçeye göre değişim |
| stok | eldeki stok (mağaza, depo) |
| cover | kaç haftalık stok |
| satis_orani | sell-through, eritme oranı |
| en_cok_satan | best seller listesi |
| en_az_satan | worst seller, satmayan |
| kirik_beden | beden kırığı, beden tamamlama |
| sevk_durumu | sevkiyat, yolda, rezerv |
| transfer | mağazalar arası transfer önerisi |
| indirim_fiyat | indirim oranı, fiyat, ASP, tam fiyat payı |
| marj | brüt marj, çarpan, GMROI |
| butce_otb | OTB, bütçe gerçekleşme, alım planı |
| magaza_siralama | mağaza performans sıralaması |
| siparis_termin | açık sipariş, termin, mal girişi |
| iade | iade oranı, iade toplama |
| kapasite | mağaza kapasitesi, doluluk, seçenek sayısı |
| kapsam_disi | konu dışı / selamlaşma |

### Slot'lar

| slot | değerler |
|---|---|
| cinsiyet | ERKEK, KADIN, ERKEK_COCUK, KIZ_COCUK, COCUK, BEBEK, TUM |
| urun_grubu | MONT, KABAN, TRIKO, KAZAK, GOMLEK, TISORT, POLO, CHINO, JEAN, PANTOLON, AYAKKABI, CORAP, CANTA, IC_GIYIM … (45 değer, `data/schema.json`) |
| donem | BUGUN, BU_HAFTA, GECEN_HAFTA, SON_4_HAFTA, BU_AY, AY:01–12, HAFTA:nn, BU_SEZON, SEZON:KIS/YAZ, YTD … |
| magaza | serbest metin (il/ilçe adı ya da 4 haneli kod); birden fazlaysa liste |
| kanal | MAGAZA, ETICARET, OUTLET, TOPTAN, KURUMSAL, PAZARYERI, SEZON_MAGAZA, TUM |
| olcu | CIRO, ADET, MARJ |
| kiyas | GY, PLAN, BUTCE, GECEN_HAFTA |
| n | tam sayı (top-N) |
| sezon | KIS, YAZ, ILKBAHAR, SONBAHAR, YENI, ESKI |

## Nasıl üretildi

Tamamen **sentetik**: her intent için elle yazılmış 11–17 Türkçe şablon, genel perakende sözlüğünden slot
doldurma (`uret.py`), yüzey çeşitlemesi (selamlama öneki, rica soneki, küçük/büyük harf). Mağaza adları Türkiye
il/ilçe adları ya da rastgele 4 haneli kodlardır; **hiçbir şirkete ait veri, mağaza, ürün kodu ya da rakam içermez.**

Sınırlar (v0.1):
- Şablon tabanlı olduğu için doğal konuşma çeşitliliği sınırlı; v0.2'de insan yazımı paraphrase eklenecek.
- Tek intent / tek soru; birleşik sorular ("satış ve cover") yok.
- Slot etiketleri kanonik değerdir, metin içi konum (span) verilmez.

## Taban çizgisi

`baseline.py`: `ytu-ce-cosmos/turkish-e5-large` embedding + en yakın merkez (nearest centroid) ve kNN;
sonuç dataset kartının altındaki tabloda (bkz. "Sonuçlar").

## Kullanım

```python
from datasets import load_dataset
ds = load_dataset("sdadsasdasdasdasd/merch-tr-intent")
print(ds["train"][0])
```

Kaynak kod ve üretici: https://github.com/retrovirusretro/merch-tr-intent

## Lisans ve atıf

CC-BY-4.0. Atıf: `merch-tr-intent (2026), Türkçe perakende merchandising intent veri seti`.

## Sonuçlar

| yöntem | test doğruluk (intent) |
|---|---|
| nearest centroid, turkish-e5-large (eğitimsiz) | 0,766 |
| kNN k=5, turkish-e5-large (eğitimsiz) | 0,576 |

Test şablonları eğitimde görülmediği için bu sayılar genellemeyi ölçer. Embedding'de slot kelimeleri (ürün, dönem)
baskın olduğundan kNN düşük kalır; eğitimli bir sınıflandırıcı ya da küçük bir dil modeli ince ayarı (LoRA) beklenen
sonraki adımdır. En çok karışan çiftler: kırık beden ↔ transfer, transfer ↔ stok, sipariş/termin ↔ sevk durumu.
Zor örnekler kasıtlıdır: bu çiftleri ayırmak asistanın asıl işidir.
