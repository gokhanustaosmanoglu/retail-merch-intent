# -*- coding: utf-8 -*-
r"""merch-tr-intent — Türkçe perakende merchandising soru → intent + slot sentetik veri seti üreteci.
Şirket verisi YOK: ürün grupları, dönemler, kanal adları genel perakende sözlüğü; mağaza adları il/ilçe + uydurma kod.
Çıktı: data/train.jsonl, data/test.jsonl, data/schema.json
Test bölmesi şablon düzeyinde ayrılır (test şablonları eğitimde hiç görülmez) → genelleme ölçülür.
"""
import json, random, re, hashlib
from pathlib import Path

random.seed(20261115)
HERE = Path(__file__).resolve().parent
OUT = HERE / "data"; OUT.mkdir(exist_ok=True)

# ---------------- SLOT SÖZLÜKLERİ (yüzey biçimi → kanonik değer) ----------------
CINSIYET = {
    "erkek": "ERKEK", "erkekte": "ERKEK", "erkek tarafında": "ERKEK", "men": "ERKEK",
    "kadın": "KADIN", "kadında": "KADIN", "bayan": "KADIN", "bayanda": "KADIN", "women": "KADIN",
    "erkek çocuk": "ERKEK_COCUK", "erkek çocukta": "ERKEK_COCUK", "kız çocuk": "KIZ_COCUK", "kız çocukta": "KIZ_COCUK",
    "çocuk": "COCUK", "çocukta": "COCUK", "kids": "COCUK", "bebek": "BEBEK",
    "tüm cinsiyetlerde": "TUM", "toplamda": "TUM", "genelde": "TUM",
}
URUN = {
    "mont": "MONT", "kaban": "KABAN", "dış giyim": "DIS_GIYIM", "yelek": "YELEK", "ceket": "CEKET", "trençkot": "TRENCKOT",
    "triko": "TRIKO", "kazak": "KAZAK", "hırka": "HIRKA", "sweatshirt": "SWEATSHIRT", "sweat": "SWEATSHIRT", "kapüşonlu": "SWEATSHIRT",
    "gömlek": "GOMLEK", "tişört": "TISORT", "t-shirt": "TISORT", "polo yaka": "POLO", "polo": "POLO", "basic tişört": "BASIC_TISORT",
    "chino": "CHINO", "jean": "JEAN", "kot pantolon": "JEAN", "pantolon": "PANTOLON", "eşofman": "ESOFMAN", "şort": "SORT",
    "elbise": "ELBISE", "etek": "ETEK", "bluz": "BLUZ", "tunik": "TUNIK", "mayo": "MAYO",
    "ayakkabı": "AYAKKABI", "sneaker": "SNEAKER", "bot": "BOT", "terlik": "TERLIK",
    "çorap": "CORAP", "kemer": "KEMER", "çanta": "CANTA", "cüzdan": "CUZDAN", "bere": "BERE", "atkı": "ATKI", "şapka": "SAPKA",
    "aksesuar": "AKSESUAR", "iç giyim": "IC_GIYIM", "pijama": "PIJAMA", "boxer": "BOXER", "parfüm": "PARFUM", "valiz": "VALIZ",
}
DONEM = {
    "bugün": "BUGUN", "dün": "DUN", "bu hafta": "BU_HAFTA", "geçen hafta": "GECEN_HAFTA", "haftalık": "BU_HAFTA",
    "son 7 gün": "SON_7_GUN", "son 7 günde": "SON_7_GUN", "son iki hafta": "SON_2_HAFTA", "son 2 hafta": "SON_2_HAFTA",
    "son 4 hafta": "SON_4_HAFTA", "son dört haftada": "SON_4_HAFTA", "bu ay": "BU_AY", "geçen ay": "GECEN_AY",
    "Ocak": "AY:01", "Şubat": "AY:02", "Mart": "AY:03", "Nisan": "AY:04", "Mayıs": "AY:05", "Haziran": "AY:06",
    "Temmuz": "AY:07", "Ağustos": "AY:08", "Eylül": "AY:09", "Ekim": "AY:10", "Kasım": "AY:11", "Aralık": "AY:12",
    "bu sezon": "BU_SEZON", "kış sezonunda": "SEZON:KIS", "yaz sezonunda": "SEZON:YAZ", "sezon başından beri": "SEZON_BASINDAN",
    "yılbaşından beri": "YTD", "yıl başından bu yana": "YTD", "YTD": "YTD",
    "42. hafta": "HAFTA:42", "45. haftada": "HAFTA:45", "W46": "HAFTA:46", "W40'ta": "HAFTA:40", "38. hafta": "HAFTA:38",
    "son çeyrekte": "SON_CEYREK", "hafta sonu": "HAFTA_SONU", "Black Friday haftasında": "HAFTA:BF",
}
MAGAZA_IL = ["Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Samsun", "Trabzon", "Eskişehir", "Gaziantep",
             "Kayseri", "Mersin", "Diyarbakır", "Denizli", "Kocaeli", "Sakarya", "Malatya", "Erzurum", "Van", "Muğla"]
MAGAZA_ILCE = ["Kadıköy", "Nişantaşı", "Bakırköy", "Beylikdüzü", "Ümraniye", "Ataşehir", "Maltepe", "Şişli", "Bağcılar", "Pendik",
               "Alsancak", "Bornova", "Nilüfer", "Çankaya", "Keçiören", "Konyaaltı", "Seyhan", "Atakum", "Selçuklu", "Tepebaşı"]
def magaza_uret():
    r = random.random()
    if r < 0.4: ad = random.choice(MAGAZA_IL) + random.choice(["", " merkez", " AVM", " outlet", " cadde"])
    elif r < 0.8: ad = random.choice(MAGAZA_ILCE) + random.choice(["", " mağazası", " AVM"])
    else: ad = str(random.randint(1001, 1999))
    return ad.strip(), ad.strip().upper().replace("MAĞAZASI", "").strip()
KANAL = {"mağazalarda": "MAGAZA", "mağaza kanalında": "MAGAZA", "e-ticarette": "ETICARET", "online": "ETICARET", "internet satışında": "ETICARET",
         "outletlerde": "OUTLET", "outlet kanalında": "OUTLET", "toptanda": "TOPTAN", "kurumsal kanalda": "KURUMSAL", "pazaryerinde": "PAZARYERI",
         "sezon mağazalarında": "SEZON_MAGAZA", "tüm kanallarda": "TUM"}
OLCU = {"ciro": "CIRO", "ciroda": "CIRO", "TL bazında": "CIRO", "adet": "ADET", "adette": "ADET", "adet bazında": "ADET", "marj": "MARJ", "brüt kârda": "MARJ"}
KIYAS = {"geçen yıla göre": "GY", "GY'ye göre": "GY", "geçen seneye göre": "GY", "LY'ye göre": "GY", "plana göre": "PLAN", "bütçeye göre": "BUTCE",
         "geçen haftaya göre": "GECEN_HAFTA", "hedefe göre": "PLAN"}
N = ["5", "10", "20", "ilk 10", "en iyi 5", "top 20"]
SEZON = {"kış": "KIS", "yaz": "YAZ", "ilkbahar": "ILKBAHAR", "sonbahar": "SONBAHAR", "yeni sezon": "YENI", "eski sezon": "ESKI", "geçen sezon": "ESKI"}

# ---------------- ŞABLONLAR ----------------
# {c}=cinsiyet {u}=ürün {d}=dönem {m}=mağaza {k}=kanal {o}=ölçü {y}=kıyas {n}=adet {s}=sezon
T = {
"satis": [
    "{c} {u} {d} kaç sattı", "{d} {c} {u} satışı ne kadar", "{u} {d} ne kadar ciro yaptı", "{c} {u} {d} {o} satışını verir misin",
    "{m} mağazasında {u} {d} kaç adet satıldı", "{k} {c} {u} {d} satış rakamı nedir", "{d} {c} toplam satış ne oldu",
    "{u} satışları {d} nasıl gitti", "{m} {d} ne kadar ciro yaptı", "{c} {d} {o} bazında satış", "{d} {u} satış adedi",
    "{c} {u} {m} mağazasında {d} kaç tane gitti", "{s} {u} satışı {d} kaç", "bana {d} {c} {u} satışını çıkar",
    "{u} {d} {k} ne kadar satmış", "{d} en fazla hangi gün satış oldu {u}", "{m} {d} {c} satışı",
],
"buyume": [
    "{c} {u} {d} {y} büyüme kaç", "{d} {c} satışı {y} ne kadar değişti", "{u} {d} {y} yüzde kaç arttı", "{m} {d} {y} nasıl",
    "{d} {y} ciro büyümesi nedir", "{c} {d} {y} geriledi mi", "{u} {y} {d} artış var mı", "{k} {d} {y} büyüme oranı",
    "{d} {c} {u} {y} fark ne kadar", "{m} mağazası {y} {d} kaç puan büyüdü", "{d} {y} adet büyümesi {c}", "{u} {d} {y} düşüş var mı",
    "{c} {d} {y} LFL büyüme", "{d} {o} {y} değişim {u}",
],
"stok": [
    "{c} {u} stoğu ne kadar", "{m} mağazasında {u} stok var mı", "depoda {c} {u} kaç adet var", "{u} mevcut stok adedi",
    "{c} {u} {m} stoğu kaç", "{k} {u} stok durumu", "{s} {u} elde ne kadar stok var", "{c} {u} depo stoğu", "{m} {c} stok kaç adet",
    "{u} toplam stok ne kadar", "{c} {u} mağaza stoğu ve depo stoğu", "elimizde ne kadar {u} var", "{m} mağazasının {c} stoğu",
    "{s} {c} stok seviyesi", "{u} stok adedi kaç {m}",
],
"cover": [
    "{c} {u} cover kaç hafta", "{u} kaç haftalık stok var", "{m} mağazasında {u} cover ne", "{c} {u} {k} cover oranı",
    "{u} stoğu kaç hafta yeter", "{c} {d} cover kaç", "{m} cover kaç hafta", "{s} {u} cover", "{c} {u} haftalık stok karşılama",
    "{u} kaç hafta gider bu stokla", "{k} {c} cover ne durumda", "{m} mağazasında {c} kaç haftalık stok var", "{u} cover yüksek mi",
],
"satis_orani": [
    "{c} {u} sell through kaç", "{u} satış oranı {d} ne", "{s} {u} sell-through yüzde kaç", "{c} {u} eritme oranı", "{m} {u} satış oranı",
    "{u} {d} eriyen stok yüzdesi", "{c} {s} sell through", "{u} ne kadarı satıldı yüzde olarak", "{k} {u} satış oranı {d}",
    "{c} {u} {d} sellthru", "{s} koleksiyonunun satış oranı", "{m} mağazasında {c} {u} kaç yüzde eridi",
],
"en_cok_satan": [
    "{c} {d} en çok satan {n} ürün", "{d} en çok satan {u} modelleri", "{m} mağazasında {d} best seller ne", "{c} {u} {d} en iyi satanlar",
    "{d} {k} top {n} seçenek", "{c} {d} hangi {u} daha çok sattı", "en çok satan {n} {u}", "{m} {d} en çok giden {c} ürünler",
    "{d} {c} best {n}", "{u} grubunda {d} lider model hangisi", "{d} en hızlı satan {c} {u}", "{s} en çok satan {n} {u}",
],
"en_az_satan": [
    "{c} {d} en az satan {n} ürün", "{d} satmayan {u} modelleri", "{m} mağazasında {d} worst seller", "{c} {u} {d} en kötü satanlar",
    "{d} {k} en yavaş {n} seçenek", "hiç satmayan {c} {u} var mı", "{d} ölü stok {u}", "{s} en az satan {n} {u}",
    "{c} {d} worst {n}", "{u} grubunda {d} en düşük satan model", "{m} {d} satmayan {c} ürünler",
],
"kirik_beden": [
    "{c} {u} kırık beden var mı", "{m} mağazasında {u} bedenleri kırık mı", "{c} {u} beden eksiği hangi mağazalarda", "{u} kırık beden oranı",
    "{m} {c} kırık beden listesi", "{c} {u} hangi bedenler eksik", "{m} mağazasında {c} kırıklık ne durumda", "{u} beden tamamlama gereken mağazalar",
    "{c} {u} {m} beden durumu", "{k} {c} {u} kırıklık", "{d} kırık bedeni olan {u} seçenekleri", "{c} {u} kırıklık oranı {m}",
    "en çok kırık {c} {u} hangi mağazada", "{u} beden kırığı var mı {m}",
],
"sevk_durumu": [
    "{m} mağazasına {u} sevki ne zaman gider", "{c} {u} sevkiyat ne durumda", "{m} mağazasına giden {u} yolda mı", "{u} sevk edildi mi {m}",
    "{c} {u} ne zaman mağazaya ulaşır", "{m} {d} kaç koli sevk edildi", "{u} depodan çıktı mı", "{m} mağazasının bekleyen sevkiyatı var mı",
    "{c} {u} {m} sevkiyat durumu", "{d} {m} mağazasına ne gönderildi", "{u} yolda ne kadar var", "{m} mağazasına {c} sevk planı ne",
    "{u} ne zaman mağazada olur", "{c} {u} sevki gecikti mi", "{m} için {u} rezerv var mı",
],
"transfer": [
    "{c} {u} için transfer önerisi var mı", "{m} mağazasından nereye {u} transfer edelim", "{u} mağazalar arası transfer listesi", "{c} {u} fazla olan mağazalar",
    "{m} mağazasına {u} transfer yapılabilir mi", "{c} {u} hangi mağazadan hangi mağazaya kaydıralım", "{u} transfer adayı mağazalar",
    "{m} fazla {c} {u} stoğunu nereye verelim", "{c} {u} dengeleme transferi", "{m} ile {m} arasında {u} transfer", "{u} transfer ihtiyacı olan mağazalar",
    "{c} {u} yeniden dağıtım önerisi", "{m} mağazasından {u} çekelim mi",
],
"indirim_fiyat": [
    "{c} {u} indirim oranı kaç", "{u} fiyatı ne", "{d} ortalama indirim yüzde kaç", "{c} {u} {d} indirim payı", "{m} mağazasında {u} fiyatı",
    "{u} kaç lira", "{c} {d} peşin indirim oranı", "{s} {u} markdown oranı", "{u} indirimde mi", "{c} {u} ortalama satış fiyatı {d}",
    "{d} {c} ASP ne kadar", "{u} fiyat noktası", "{k} {d} indirim oranı", "{c} {u} fiyat listesi", "{u} tam fiyat satış payı {d}",
],
"marj": [
    "{c} {u} brüt marj kaç", "{d} marj oranı ne", "{u} GMROI kaç", "{c} {d} kârlılık", "{m} mağazasının {d} marjı", "{u} {d} çarpan kaç",
    "{c} {u} {d} brüt kâr", "{k} {d} marj", "{s} {u} marj oranı", "{c} {d} marj {y} değişti mi", "{u} maliyet üzerinden çarpan",
    "{d} {c} kâr marjı yüzde kaç", "{u} marj düşük mü",
],
"butce_otb": [
    "{c} {u} OTB ne kadar", "{d} bütçeye göre durum ne", "{s} {c} açık bütçe var mı", "{u} alım bütçesi kaldı mı", "{c} {d} bütçe gerçekleşme oranı",
    "{s} OTB kaç", "{c} {u} plan gerçekleşen farkı", "{d} ciro bütçesi tuttu mu", "{k} {d} bütçe sapması", "{c} {s} alım planı ne kadar",
    "{u} için ek alım yapabilir miyiz", "{d} {c} plan ne kadardı", "{s} bütçe kullanımı yüzde kaç",
],
"magaza_siralama": [
    "{d} en iyi {n} mağaza", "{c} {d} mağaza sıralaması", "{m} mağazası {d} kaçıncı sırada", "{d} en kötü {n} mağaza", "{c} {u} satışında en iyi mağazalar",
    "{d} mağaza performans listesi", "{m} mağazasının {d} performansı nasıl", "{d} {y} en çok büyüyen mağazalar", "{c} {d} en düşük {n} mağaza",
    "{u} satışında {m} kaçıncı", "{d} metrekare verimi en yüksek mağazalar", "{d} ciroya göre mağaza listesi", "{c} {m} {d} hedef tutturdu mu",
],
"siparis_termin": [
    "{c} {u} siparişi ne zaman gelir", "{s} {u} termin tarihi ne", "{c} {u} açık sipariş ne kadar", "{u} tedarikçi gecikmesi var mı",
    "{s} {c} mal girişi ne zaman", "{u} siparişinin ne kadarı geldi", "{c} {u} teslimat yüzdesi", "{d} gelen mal adedi {c}", "{u} termini kaydı mı",
    "{s} {u} ne kadarı depoya girdi", "{c} {u} bekleyen sipariş", "{u} repeat siparişi yetişir mi", "{s} {c} sipariş durumu",
],
"iade": [
    "{c} {u} iade oranı kaç", "{m} mağazasının {d} iadesi ne kadar", "{d} iade adedi {c}", "{s} iade ne zaman toplanacak", "{u} iade yüzdesi {d}",
    "{m} {s} iadesi tamamlandı mı", "{c} {d} mağaza iadeleri", "{s} ürünlerin iadesi hangi mağazalarda kaldı", "{d} e-ticaret iade oranı {u}",
    "{c} {u} iade nedenleri", "{m} mağazasının bekleyen iadesi var mı", "{s} iade sonrası kalan {c} stok",
],
"kapasite": [
    "{m} mağazasının {c} kapasitesi ne", "{c} {u} için mağaza kapasitesi yeter mi", "{m} doluluk oranı kaç", "{c} {m} kaç seçenek alabilir",
    "{m} mağazasında {c} askı kapasitesi", "{u} için {m} kapasite var mı", "{c} kapasite doluluğu {d}", "{m} seçenek sayısı planı ne",
    "{c} {u} {m} asorti planı", "{m} mağazası {c} kaç adet taşır", "{c} {d} doluluk yüksek mağazalar", "{m} {c} kapasite aşımı var mı",
],
"kapsam_disi": [
    "merhaba nasılsın", "bugün hava nasıl", "saat kaç", "teşekkürler", "iyi çalışmalar", "toplantı kaçta", "yemek listesi ne", "bana bir fıkra anlat",
    "dolar kuru kaç", "yarın tatil mi", "bilgisayarım açılmıyor", "şifremi unuttum", "trafik nasıl", "bu hafta sonu ne yapsam", "selam",
    "görüşürüz", "ok tamam", "bu doğru mu", "anlamadım tekrar eder misin", "yardım", "yazıcı çalışmıyor", "izin formu nerede",
    "maaş ne zaman yatar", "kargo takip numarası nerede yazar", "futbol maçı kaçta", "en yakın eczane",
],
}

ONEK = ["", "", "", "", "Merhaba, ", "Selam, ", "Acil: ", "Hızlıca ", "Bir bakar mısın, ", "Soru: ", "Kısaca ", "Lütfen "]
SONEK = ["", "", "", "?", "?", " ?", " lütfen", " bakar mısın", " paylaşır mısın", " çıkarır mısın", " söyler misin", " rica ederim", " acil"]

def kanon(val, sozluk): return sozluk[val]

def doldur(sablon, intent):
    slots = {}
    text = sablon
    def sec(key, sozluk):
        k = random.choice(list(sozluk)); return k, sozluk[k]
    if "{c}" in text:
        k, v = sec("c", CINSIYET); text = text.replace("{c}", k); slots["cinsiyet"] = v
    if "{u}" in text:
        k, v = sec("u", URUN); text = text.replace("{u}", k); slots["urun_grubu"] = v
    if "{d}" in text:
        k, v = sec("d", DONEM); text = text.replace("{d}", k); slots["donem"] = v
    while "{m}" in text:
        ad, v = magaza_uret(); text = text.replace("{m}", ad, 1); slots.setdefault("magaza", []).append(v)
    if "{k}" in text:
        k, v = sec("k", KANAL); text = text.replace("{k}", k); slots["kanal"] = v
    if "{o}" in text:
        k, v = sec("o", OLCU); text = text.replace("{o}", k); slots["olcu"] = v
    if "{y}" in text:
        k, v = sec("y", KIYAS); text = text.replace("{y}", k); slots["kiyas"] = v
    if "{n}" in text:
        k = random.choice(N); text = text.replace("{n}", k); slots["n"] = int(re.sub(r"\D", "", k))
    if "{s}" in text:
        k, v = sec("s", SEZON); text = text.replace("{s}", k); slots["sezon"] = v
    if "magaza" in slots and len(slots["magaza"]) == 1: slots["magaza"] = slots["magaza"][0]
    # yüzey çeşitlemesi: şablon zaten soru ekiyle/fiille bitiyorsa yalnız "?" eklenir
    soru_bitis = re.search(r"\b(mı|mi|mu|mü|mısın|misin|miyiz|mıyız|musun|müsün|verir misin|var mı)$", text.strip())
    sonek = random.choice(["", "", "?", "?"]) if soru_bitis else random.choice(SONEK)
    onek = random.choice(ONEK)
    if onek.strip().lower() == "lütfen" and "lütfen" in sonek: sonek = ""
    text = onek + text + sonek
    r = random.random()
    if r < 0.25: text = text.lower()
    elif r < 0.35: text = text[0].upper() + text[1:]
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+\?", "?", text)
    return text, slots

def main():
    HEDEF = {i: (60 if i == "kapsam_disi" else 150) for i in T}
    kayit, gorulen = [], set()
    test_sablon = {}
    for intent, sablonlar in T.items():
        s = sablonlar[:]; random.shuffle(s)
        n_test = max(1, round(len(s) * 0.2)) if intent != "kapsam_disi" else 0
        test_sablon[intent] = set(s[:n_test])
    for intent, sablonlar in T.items():
        say = 0; deneme = 0
        while say < HEDEF[intent] and deneme < HEDEF[intent] * 20:
            deneme += 1
            sab = random.choice(sablonlar)
            if intent == "kapsam_disi":
                text = random.choice(["", "", "", "Merhaba, ", "Selam, "]) + sab + random.choice(["", "", "?", "!", "."]); text = re.sub(r"\s+\?", "?", text).strip(); slots = {}
                if random.random() < 0.3: text = text.lower()
                elif random.random() < 0.5: text = text[0].upper() + text[1:]
            else:
                text, slots = doldur(sab, intent)
            key = text.lower()
            if key in gorulen: continue
            gorulen.add(key); say += 1
            split = "test" if sab in test_sablon[intent] else "train"
            kayit.append({"id": hashlib.md5(key.encode()).hexdigest()[:10], "text": text, "intent": intent, "slots": slots, "template_split": split})
    random.shuffle(kayit)
    train = [k for k in kayit if k["template_split"] == "train"]
    test = [k for k in kayit if k["template_split"] == "test"]
    # kapsam_disi için rastgele %15 test
    kd = [k for k in train if k["intent"] == "kapsam_disi"]; random.shuffle(kd)
    for k in kd[: round(len(kd) * 0.15)]:
        train.remove(k); k["template_split"] = "test"; test.append(k)
    for ad, veri in (("train", train), ("test", test)):
        with open(OUT / f"{ad}.jsonl", "w", encoding="utf-8") as f:
            for k in veri:
                k2 = {kk: vv for kk, vv in k.items() if kk != "template_split"}
                f.write(json.dumps(k2, ensure_ascii=False) + "\n")
    schema = {
        "intents": {i: len([k for k in kayit if k["intent"] == i]) for i in T},
        "slots": {
            "cinsiyet": sorted(set(CINSIYET.values())), "urun_grubu": sorted(set(URUN.values())), "donem": sorted(set(DONEM.values())),
            "magaza": "serbest metin (il/ilçe adı ya da 4 haneli kod); birden fazla ise liste", "kanal": sorted(set(KANAL.values())),
            "olcu": sorted(set(OLCU.values())), "kiyas": sorted(set(KIYAS.values())), "n": "tam sayı", "sezon": sorted(set(SEZON.values())),
        },
        "split": "test şablonları eğitimde görülmez (template-level holdout)",
        "train": len(train), "test": len(test), "templates": {i: len(s) for i, s in T.items()},
    }
    (OUT / "schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"train {len(train)} · test {len(test)} · intent {len(T)}")
    for i in T: print(f"  {i:16s} {schema['intents'][i]:4d}  şablon {len(T[i])}")
    for k in random.sample(kayit, 8): print(" ", k["intent"], "|", k["text"], "|", k["slots"])

if __name__ == "__main__":
    main()
