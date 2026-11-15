# -*- coding: utf-8 -*-
r"""merch-tr-intent v0.2 — retail merchandising question -> intent + slot dataset generator (Turkish + English).

Both languages share ONE schema: same 18 intents, same 9 slots, same English canonical slot values.
Templates are written independently per language (not machine-translated), so the two sides are
"schema-parallel", not sentence-parallel.

No company data: product groups, periods and channels come from a generic retail vocabulary; store
names are city / district names or random 4-digit codes.

Output:
  data/tr/train.jsonl, data/tr/test.jsonl
  data/en/train.jsonl, data/en/test.jsonl
  data/schema.json
Test split is template-level: test templates are never seen in training -> measures generalisation.
"""
import json, random, re, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data"

# ======================= SHARED CANONICAL VALUES (English) =======================
MONTHS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

# ======================= TURKISH LEXICON (surface -> canonical) =======================
TR = {}
TR["gender"] = {
    "erkek": "MEN", "erkekte": "MEN", "erkek tarafında": "MEN", "men": "MEN",
    "kadın": "WOMEN", "kadında": "WOMEN", "bayan": "WOMEN", "bayanda": "WOMEN", "women": "WOMEN",
    "erkek çocuk": "BOYS", "erkek çocukta": "BOYS", "kız çocuk": "GIRLS", "kız çocukta": "GIRLS",
    "çocuk": "KIDS", "çocukta": "KIDS", "kids": "KIDS", "bebek": "BABY",
    "tüm cinsiyetlerde": "ALL", "toplamda": "ALL", "genelde": "ALL",
}
TR["product_group"] = {
    "mont": "COAT", "kaban": "OVERCOAT", "dış giyim": "OUTERWEAR", "yelek": "VEST", "ceket": "JACKET", "trençkot": "TRENCH_COAT",
    "triko": "KNITWEAR", "kazak": "SWEATER", "hırka": "CARDIGAN", "sweatshirt": "SWEATSHIRT", "sweat": "SWEATSHIRT", "kapüşonlu": "SWEATSHIRT",
    "gömlek": "SHIRT", "tişört": "TSHIRT", "t-shirt": "TSHIRT", "polo yaka": "POLO", "polo": "POLO", "basic tişört": "BASIC_TSHIRT",
    "chino": "CHINO", "jean": "JEANS", "kot pantolon": "JEANS", "pantolon": "TROUSERS", "eşofman": "TRACKSUIT", "şort": "SHORTS",
    "elbise": "DRESS", "etek": "SKIRT", "bluz": "BLOUSE", "tunik": "TUNIC", "mayo": "SWIMWEAR",
    "ayakkabı": "SHOES", "sneaker": "SNEAKERS", "bot": "BOOTS", "terlik": "SLIPPERS",
    "çorap": "SOCKS", "kemer": "BELT", "çanta": "BAG", "cüzdan": "WALLET", "bere": "BEANIE", "atkı": "SCARF", "şapka": "HAT",
    "aksesuar": "ACCESSORIES", "iç giyim": "UNDERWEAR", "pijama": "PYJAMAS", "boxer": "BOXERS", "parfüm": "FRAGRANCE", "valiz": "LUGGAGE",
}
TR["period"] = {
    "bugün": "TODAY", "dün": "YESTERDAY", "bu hafta": "THIS_WEEK", "geçen hafta": "LAST_WEEK", "haftalık": "THIS_WEEK",
    "son 7 gün": "LAST_7_DAYS", "son 7 günde": "LAST_7_DAYS", "son iki hafta": "LAST_2_WEEKS", "son 2 hafta": "LAST_2_WEEKS",
    "son 4 hafta": "LAST_4_WEEKS", "son dört haftada": "LAST_4_WEEKS", "bu ay": "THIS_MONTH", "geçen ay": "LAST_MONTH",
    "bu sezon": "THIS_SEASON", "kış sezonunda": "SEASON:WINTER", "yaz sezonunda": "SEASON:SUMMER", "sezon başından beri": "SEASON_TO_DATE",
    "yılbaşından beri": "YTD", "yıl başından bu yana": "YTD", "YTD": "YTD",
    "42. hafta": "WEEK:42", "45. haftada": "WEEK:45", "W46": "WEEK:46", "W40'ta": "WEEK:40", "38. hafta": "WEEK:38",
    "son çeyrekte": "LAST_QUARTER", "hafta sonu": "WEEKEND", "Black Friday haftasında": "WEEK:BLACK_FRIDAY",
}
for i, ay in enumerate(["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]):
    TR["period"][ay] = f"MONTH:{MONTHS[i]}"
TR["channel"] = {"mağazalarda": "STORES", "mağaza kanalında": "STORES", "e-ticarette": "ECOMMERCE", "online": "ECOMMERCE", "internet satışında": "ECOMMERCE",
                 "outletlerde": "OUTLET", "outlet kanalında": "OUTLET", "toptanda": "WHOLESALE", "kurumsal kanalda": "CONCESSION", "pazaryerinde": "MARKETPLACE",
                 "sezon mağazalarında": "FULL_PRICE_STORES", "tüm kanallarda": "ALL"}
TR["measure"] = {"ciro": "REVENUE", "ciroda": "REVENUE", "TL bazında": "REVENUE", "adet": "UNITS", "adette": "UNITS", "adet bazında": "UNITS", "marj": "MARGIN", "brüt kârda": "MARGIN"}
TR["comparison"] = {"geçen yıla göre": "LY", "GY'ye göre": "LY", "geçen seneye göre": "LY", "LY'ye göre": "LY", "plana göre": "PLAN", "bütçeye göre": "BUDGET",
                    "geçen haftaya göre": "LAST_WEEK", "hedefe göre": "PLAN"}
TR["season"] = {"kış": "WINTER", "yaz": "SUMMER", "ilkbahar": "SPRING", "sonbahar": "AUTUMN", "yeni sezon": "NEW", "eski sezon": "OLD", "geçen sezon": "OLD"}
TR["n"] = ["5", "10", "20", "ilk 10", "en iyi 5", "top 20"]
TR["store_city"] = ["Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Samsun", "Trabzon", "Eskişehir", "Gaziantep",
                    "Kayseri", "Mersin", "Diyarbakır", "Denizli", "Kocaeli", "Sakarya", "Malatya", "Erzurum", "Van", "Muğla"]
TR["store_district"] = ["Kadıköy", "Nişantaşı", "Bakırköy", "Beylikdüzü", "Ümraniye", "Ataşehir", "Maltepe", "Şişli", "Bağcılar", "Pendik",
                        "Alsancak", "Bornova", "Nilüfer", "Çankaya", "Keçiören", "Konyaaltı", "Seyhan", "Atakum", "Selçuklu", "Tepebaşı"]
TR["store_suffix_a"] = ["", " merkez", " AVM", " outlet", " cadde"]
TR["store_suffix_b"] = ["", " mağazası", " AVM"]
TR["prefix"] = ["", "", "", "", "Merhaba, ", "Selam, ", "Acil: ", "Hızlıca ", "Bir bakar mısın, ", "Soru: ", "Kısaca ", "Lütfen "]
TR["suffix"] = ["", "", "", "?", "?", " ?", " lütfen", " bakar mısın", " paylaşır mısın", " çıkarır mısın", " söyler misin", " rica ederim", " acil"]
TR["question_end"] = r"\b(mı|mi|mu|mü|mısın|misin|miyiz|mıyız|musun|müsün|verir misin|var mı)$"

TR["templates"] = {
"sales": [
    "{c} {u} {d} kaç sattı", "{d} {c} {u} satışı ne kadar", "{u} {d} ne kadar ciro yaptı", "{c} {u} {d} {o} satışını verir misin",
    "{m} mağazasında {u} {d} kaç adet satıldı", "{k} {c} {u} {d} satış rakamı nedir", "{d} {c} toplam satış ne oldu",
    "{u} satışları {d} nasıl gitti", "{m} {d} ne kadar ciro yaptı", "{c} {d} {o} bazında satış", "{d} {u} satış adedi",
    "{c} {u} {m} mağazasında {d} kaç tane gitti", "{s} {u} satışı {d} kaç", "bana {d} {c} {u} satışını çıkar",
    "{u} {d} {k} ne kadar satmış", "{d} en fazla hangi gün satış oldu {u}", "{m} {d} {c} satışı",
],
"growth": [
    "{c} {u} {d} {y} büyüme kaç", "{d} {c} satışı {y} ne kadar değişti", "{u} {d} {y} yüzde kaç arttı", "{m} {d} {y} nasıl",
    "{d} {y} ciro büyümesi nedir", "{c} {d} {y} geriledi mi", "{u} {y} {d} artış var mı", "{k} {d} {y} büyüme oranı",
    "{d} {c} {u} {y} fark ne kadar", "{m} mağazası {y} {d} kaç puan büyüdü", "{d} {y} adet büyümesi {c}", "{u} {d} {y} düşüş var mı",
    "{c} {d} {y} LFL büyüme", "{d} {o} {y} değişim {u}",
],
"stock": [
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
"sell_through": [
    "{c} {u} sell through kaç", "{u} satış oranı {d} ne", "{s} {u} sell-through yüzde kaç", "{c} {u} eritme oranı", "{m} {u} satış oranı",
    "{u} {d} eriyen stok yüzdesi", "{c} {s} sell through", "{u} ne kadarı satıldı yüzde olarak", "{k} {u} satış oranı {d}",
    "{c} {u} {d} sellthru", "{s} koleksiyonunun satış oranı", "{m} mağazasında {c} {u} kaç yüzde eridi",
],
"top_sellers": [
    "{c} {d} en çok satan {n} ürün", "{d} en çok satan {u} modelleri", "{m} mağazasında {d} best seller ne", "{c} {u} {d} en iyi satanlar",
    "{d} {k} top {n} seçenek", "{c} {d} hangi {u} daha çok sattı", "en çok satan {n} {u}", "{m} {d} en çok giden {c} ürünler",
    "{d} {c} best {n}", "{u} grubunda {d} lider model hangisi", "{d} en hızlı satan {c} {u}", "{s} en çok satan {n} {u}",
],
"worst_sellers": [
    "{c} {d} en az satan {n} ürün", "{d} satmayan {u} modelleri", "{m} mağazasında {d} worst seller", "{c} {u} {d} en kötü satanlar",
    "{d} {k} en yavaş {n} seçenek", "hiç satmayan {c} {u} var mı", "{d} ölü stok {u}", "{s} en az satan {n} {u}",
    "{c} {d} worst {n}", "{u} grubunda {d} en düşük satan model", "{m} {d} satmayan {c} ürünler",
],
"broken_sizes": [
    "{c} {u} kırık beden var mı", "{m} mağazasında {u} bedenleri kırık mı", "{c} {u} beden eksiği hangi mağazalarda", "{u} kırık beden oranı",
    "{m} {c} kırık beden listesi", "{c} {u} hangi bedenler eksik", "{m} mağazasında {c} kırıklık ne durumda", "{u} beden tamamlama gereken mağazalar",
    "{c} {u} {m} beden durumu", "{k} {c} {u} kırıklık", "{d} kırık bedeni olan {u} seçenekleri", "{c} {u} kırıklık oranı {m}",
    "en çok kırık {c} {u} hangi mağazada", "{u} beden kırığı var mı {m}",
],
"shipment_status": [
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
"price_discount": [
    "{c} {u} indirim oranı kaç", "{u} fiyatı ne", "{d} ortalama indirim yüzde kaç", "{c} {u} {d} indirim payı", "{m} mağazasında {u} fiyatı",
    "{u} kaç lira", "{c} {d} peşin indirim oranı", "{s} {u} markdown oranı", "{u} indirimde mi", "{c} {u} ortalama satış fiyatı {d}",
    "{d} {c} ASP ne kadar", "{u} fiyat noktası", "{k} {d} indirim oranı", "{c} {u} fiyat listesi", "{u} tam fiyat satış payı {d}",
],
"margin": [
    "{c} {u} brüt marj kaç", "{d} marj oranı ne", "{u} GMROI kaç", "{c} {d} kârlılık", "{m} mağazasının {d} marjı", "{u} {d} çarpan kaç",
    "{c} {u} {d} brüt kâr", "{k} {d} marj", "{s} {u} marj oranı", "{c} {d} marj {y} değişti mi", "{u} maliyet üzerinden çarpan",
    "{d} {c} kâr marjı yüzde kaç", "{u} marj düşük mü",
],
"budget_otb": [
    "{c} {u} OTB ne kadar", "{d} bütçeye göre durum ne", "{s} {c} açık bütçe var mı", "{u} alım bütçesi kaldı mı", "{c} {d} bütçe gerçekleşme oranı",
    "{s} OTB kaç", "{c} {u} plan gerçekleşen farkı", "{d} ciro bütçesi tuttu mu", "{k} {d} bütçe sapması", "{c} {s} alım planı ne kadar",
    "{u} için ek alım yapabilir miyiz", "{d} {c} plan ne kadardı", "{s} bütçe kullanımı yüzde kaç",
],
"store_ranking": [
    "{d} en iyi {n} mağaza", "{c} {d} mağaza sıralaması", "{m} mağazası {d} kaçıncı sırada", "{d} en kötü {n} mağaza", "{c} {u} satışında en iyi mağazalar",
    "{d} mağaza performans listesi", "{m} mağazasının {d} performansı nasıl", "{d} {y} en çok büyüyen mağazalar", "{c} {d} en düşük {n} mağaza",
    "{u} satışında {m} kaçıncı", "{d} metrekare verimi en yüksek mağazalar", "{d} ciroya göre mağaza listesi", "{c} {m} {d} hedef tutturdu mu",
],
"order_eta": [
    "{c} {u} siparişi ne zaman gelir", "{s} {u} termin tarihi ne", "{c} {u} açık sipariş ne kadar", "{u} tedarikçi gecikmesi var mı",
    "{s} {c} mal girişi ne zaman", "{u} siparişinin ne kadarı geldi", "{c} {u} teslimat yüzdesi", "{d} gelen mal adedi {c}", "{u} termini kaydı mı",
    "{s} {u} ne kadarı depoya girdi", "{c} {u} bekleyen sipariş", "{u} repeat siparişi yetişir mi", "{s} {c} sipariş durumu",
],
"returns": [
    "{c} {u} iade oranı kaç", "{m} mağazasının {d} iadesi ne kadar", "{d} iade adedi {c}", "{s} iade ne zaman toplanacak", "{u} iade yüzdesi {d}",
    "{m} {s} iadesi tamamlandı mı", "{c} {d} mağaza iadeleri", "{s} ürünlerin iadesi hangi mağazalarda kaldı", "{d} e-ticaret iade oranı {u}",
    "{c} {u} iade nedenleri", "{m} mağazasının bekleyen iadesi var mı", "{s} iade sonrası kalan {c} stok",
],
"capacity": [
    "{m} mağazasının {c} kapasitesi ne", "{c} {u} için mağaza kapasitesi yeter mi", "{m} doluluk oranı kaç", "{c} {m} kaç seçenek alabilir",
    "{m} mağazasında {c} askı kapasitesi", "{u} için {m} kapasite var mı", "{c} kapasite doluluğu {d}", "{m} seçenek sayısı planı ne",
    "{c} {u} {m} asorti planı", "{m} mağazası {c} kaç adet taşır", "{c} {d} doluluk yüksek mağazalar", "{m} {c} kapasite aşımı var mı",
],
"out_of_scope": [
    "merhaba nasılsın", "bugün hava nasıl", "saat kaç", "teşekkürler", "iyi çalışmalar", "toplantı kaçta", "yemek listesi ne", "bana bir fıkra anlat",
    "dolar kuru kaç", "yarın tatil mi", "bilgisayarım açılmıyor", "şifremi unuttum", "trafik nasıl", "bu hafta sonu ne yapsam", "selam",
    "görüşürüz", "ok tamam", "bu doğru mu", "anlamadım tekrar eder misin", "yardım", "yazıcı çalışmıyor", "izin formu nerede",
    "maaş ne zaman yatar", "kargo takip numarası nerede yazar", "futbol maçı kaçta", "en yakın eczane",
],
}

# ======================= ENGLISH LEXICON (surface -> canonical) =======================
EN = {}
EN["gender"] = {
    "men's": "MEN", "menswear": "MEN", "mens": "MEN", "women's": "WOMEN", "womenswear": "WOMEN", "ladies'": "WOMEN",
    "boys'": "BOYS", "boyswear": "BOYS", "girls'": "GIRLS", "girlswear": "GIRLS", "kids'": "KIDS", "kidswear": "KIDS", "children's": "KIDS",
    "baby": "BABY", "total": "ALL", "all-department": "ALL",
}
EN["product_group"] = {
    "coats": "COAT", "coat": "COAT", "overcoats": "OVERCOAT", "outerwear": "OUTERWEAR", "gilets": "VEST", "vests": "VEST", "jackets": "JACKET",
    "trench coats": "TRENCH_COAT", "knitwear": "KNITWEAR", "sweaters": "SWEATER", "jumpers": "SWEATER", "cardigans": "CARDIGAN",
    "sweatshirts": "SWEATSHIRT", "hoodies": "SWEATSHIRT", "shirts": "SHIRT", "t-shirts": "TSHIRT", "tees": "TSHIRT", "polos": "POLO",
    "polo shirts": "POLO", "basic tees": "BASIC_TSHIRT", "chinos": "CHINO", "jeans": "JEANS", "denim": "JEANS", "trousers": "TROUSERS",
    "pants": "TROUSERS", "tracksuits": "TRACKSUIT", "joggers": "TRACKSUIT", "shorts": "SHORTS", "dresses": "DRESS", "skirts": "SKIRT",
    "blouses": "BLOUSE", "tunics": "TUNIC", "swimwear": "SWIMWEAR", "shoes": "SHOES", "footwear": "SHOES", "sneakers": "SNEAKERS",
    "trainers": "SNEAKERS", "boots": "BOOTS", "slippers": "SLIPPERS", "socks": "SOCKS", "belts": "BELT", "bags": "BAG", "handbags": "BAG",
    "wallets": "WALLET", "beanies": "BEANIE", "scarves": "SCARF", "hats": "HAT", "caps": "HAT", "accessories": "ACCESSORIES",
    "underwear": "UNDERWEAR", "pyjamas": "PYJAMAS", "boxers": "BOXERS", "fragrance": "FRAGRANCE", "luggage": "LUGGAGE",
}
EN["period"] = {
    "today": "TODAY", "yesterday": "YESTERDAY", "this week": "THIS_WEEK", "last week": "LAST_WEEK", "week to date": "THIS_WEEK", "WTD": "THIS_WEEK",
    "in the last 7 days": "LAST_7_DAYS", "last 7 days": "LAST_7_DAYS", "last two weeks": "LAST_2_WEEKS", "last 4 weeks": "LAST_4_WEEKS",
    "L4W": "LAST_4_WEEKS", "this month": "THIS_MONTH", "MTD": "THIS_MONTH", "last month": "LAST_MONTH",
    "this season": "THIS_SEASON", "in the winter season": "SEASON:WINTER", "this summer season": "SEASON:SUMMER",
    "season to date": "SEASON_TO_DATE", "STD": "SEASON_TO_DATE", "year to date": "YTD", "YTD": "YTD",
    "week 42": "WEEK:42", "in week 45": "WEEK:45", "W46": "WEEK:46", "wk40": "WEEK:40", "week 38": "WEEK:38",
    "last quarter": "LAST_QUARTER", "over the weekend": "WEEKEND", "Black Friday week": "WEEK:BLACK_FRIDAY",
}
for i, mo in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]):
    EN["period"][f"in {mo}"] = f"MONTH:{MONTHS[i]}"
EN["channel"] = {"in stores": "STORES", "in retail": "STORES", "online": "ECOMMERCE", "on e-commerce": "ECOMMERCE", "in outlets": "OUTLET",
                 "outlet": "OUTLET", "wholesale": "WHOLESALE", "in concessions": "CONCESSION", "on marketplaces": "MARKETPLACE",
                 "in full-price stores": "FULL_PRICE_STORES", "across all channels": "ALL"}
EN["measure"] = {"revenue": "REVENUE", "sales value": "REVENUE", "in units": "UNITS", "units": "UNITS", "margin": "MARGIN", "gross profit": "MARGIN"}
EN["comparison"] = {"vs last year": "LY", "vs LY": "LY", "versus last year": "LY", "vs plan": "PLAN", "against budget": "BUDGET",
                    "vs budget": "BUDGET", "vs last week": "LAST_WEEK", "against target": "PLAN"}
EN["season"] = {"winter": "WINTER", "summer": "SUMMER", "spring": "SPRING", "autumn": "AUTUMN", "fall": "AUTUMN", "new season": "NEW",
                "old season": "OLD", "last season": "OLD"}
EN["n"] = ["5", "10", "20", "top 10", "top 5", "top 20"]
EN["store_city"] = ["Manchester", "Lyon", "Munich", "Madrid", "Milan", "Rotterdam", "Warsaw", "Dublin", "Istanbul", "Ankara",
                    "Izmir", "Leeds", "Hamburg", "Porto", "Vienna", "Prague", "Athens", "Lisbon", "Brussels", "Copenhagen"]
EN["store_district"] = ["Oxford Street", "Westfield", "Bluewater", "La Defense", "Kadikoy", "Nisantasi", "Soho", "Covent Garden",
                        "Canary Wharf", "Kings Road", "Old Town", "Central Mall", "Airport", "Harbour", "Riverside", "City Centre"]
EN["store_suffix_a"] = ["", " flagship", " mall", " outlet", " high street"]
EN["store_suffix_b"] = ["", " store", " branch"]
EN["prefix"] = ["", "", "", "", "Hi, ", "Hey, ", "Quick one: ", "Can you check ", "Please ", "Q: ", "Urgent: "]
EN["suffix"] = ["", "", "", "?", "?", " please", " pls", " asap", " thanks", " today"]
EN["question_end"] = r"\b(is|are|do|does|did|can|will|has|have)\b.*$"

EN["templates"] = {
"sales": [
    "how many {u} did {c} sell {d}", "{c} {u} sales {d}", "what were {d} {c} {u} sales", "{u} {o} {d}",
    "how many units of {u} sold in {m} {d}", "{k} {c} {u} sales figure {d}", "total {c} sales {d}", "how did {u} sell {d}",
    "{m} revenue {d}", "{c} sales in {o} {d}", "{d} {u} units sold", "give me {d} {c} {u} sales", "{s} {u} sales {d}",
    "{u} sales {k} {d}", "what did {m} take {d}",
],
"growth": [
    "{c} {u} growth {y} {d}", "how did {d} {c} sales change {y}", "{u} {d} {y} percentage change", "how is {m} doing {y} {d}",
    "{d} revenue growth {y}", "are {c} sales down {y} {d}", "is {u} up or down {y} {d}", "{k} growth rate {d} {y}",
    "{d} {c} {u} variance {y}", "{c} LFL growth {d} {y}", "{d} {o} change {y} for {u}", "{u} unit growth {y} {d}",
    "{m} like for like {y} {d}",
],
"stock": [
    "how much {c} {u} stock do we have", "is there {u} stock in {m}", "{c} {u} warehouse stock", "{u} stock on hand",
    "{c} {u} stock in {m}", "{k} {u} stock position", "{s} {u} inventory", "current {c} {u} stock level",
    "how many {u} do we have left", "{m} {c} stock units", "{u} total inventory", "store and DC stock for {c} {u}",
    "{s} {c} stock level", "{u} SOH at {m}",
],
"cover": [
    "{c} {u} weeks of cover", "how many weeks of stock for {u}", "cover for {u} in {m}", "{k} {c} {u} cover",
    "how long will {u} stock last", "{c} cover {d}", "{m} weeks cover", "{s} {u} cover", "{u} WOC",
    "is {u} cover too high", "{k} {c} cover status", "how many weeks of {c} stock in {m}", "{c} {u} forward cover",
],
"sell_through": [
    "{c} {u} sell through", "{u} sell-through {d}", "{s} {u} sell through percentage", "{c} {u} ST {d}", "{m} {u} sell-through rate",
    "what percentage of {u} has sold", "{c} {s} sell-through", "{k} {u} sell through {d}", "{s} collection sell-through",
    "how much of the {u} buy has sold through", "{c} {u} sellthru {d}", "{m} {c} {u} sell through to date",
],
"top_sellers": [
    "top {n} {c} products {d}", "best selling {u} {d}", "{m} best sellers {d}", "{c} {u} bestsellers {d}",
    "{d} {k} top {n} options", "which {u} sold best {d}", "best {n} {u}", "top selling {c} styles in {m} {d}",
    "{d} {c} best {n}", "fastest selling {c} {u} {d}", "{s} top {n} {u}", "leading {u} style {d}",
],
"worst_sellers": [
    "worst {n} {c} products {d}", "{u} not selling {d}", "{m} worst sellers {d}", "{c} {u} bottom sellers {d}",
    "{d} {k} slowest {n} options", "any {c} {u} with zero sales", "{d} dead stock in {u}", "{s} bottom {n} {u}",
    "{c} {d} worst {n}", "lowest selling {u} style {d}", "slow movers {c} {m} {d}",
],
"broken_sizes": [
    "{c} {u} broken sizes", "are {u} sizes broken in {m}", "which stores are missing {c} {u} sizes", "{u} size break rate",
    "{m} {c} broken size list", "which {c} {u} sizes are out", "{m} {c} size gaps", "stores needing {u} size replenishment",
    "{c} {u} size curve status in {m}", "{k} {c} {u} broken sizes", "{u} options with broken sizes {d}", "{c} {u} size fragmentation in {m}",
],
"shipment_status": [
    "when will {u} ship to {m}", "{c} {u} delivery status", "is the {u} for {m} in transit", "has {u} been dispatched to {m}",
    "when will {c} {u} reach stores", "how many cartons went to {m} {d}", "has {u} left the DC", "any pending deliveries for {m}",
    "{c} {u} {m} shipment status", "what was sent to {m} {d}", "{u} in transit quantity", "{m} {c} allocation plan",
    "is {u} reserved for {m}",
],
"transfer": [
    "transfer suggestions for {c} {u}", "where should {m} send its {u}", "{u} store to store transfer list", "stores overstocked on {c} {u}",
    "can we transfer {u} to {m}", "rebalance {c} {u} between stores", "{u} transfer candidates", "move excess {c} {u} from {m}",
    "{c} {u} redistribution plan", "{u} transfer between {m} and {m}", "which stores need a {u} transfer", "should we pull {u} from {m}",
],
"price_discount": [
    "{c} {u} discount rate", "what is the price of {u}", "average markdown {d}", "{c} {u} discount depth {d}", "{u} price in {m}",
    "how much is {u}", "{c} {d} markdown percentage", "{s} {u} markdown rate", "is {u} on promotion", "{c} {u} ASP {d}",
    "{d} {c} average selling price", "{u} price points", "{k} {d} discount rate", "{u} full price sales share {d}",
],
"margin": [
    "{c} {u} gross margin", "{d} margin percentage", "{u} GMROI", "{c} profitability {d}", "{m} margin {d}", "{u} markup {d}",
    "{c} {u} gross profit {d}", "{k} margin {d}", "{s} {u} margin rate", "has {c} margin changed {y} {d}", "{u} intake margin",
    "{d} {c} margin rate", "is {u} margin too low",
],
"budget_otb": [
    "{c} {u} open to buy", "how are we tracking against budget {d}", "{s} {c} OTB remaining", "{u} buy budget left",
    "{c} {d} budget achievement", "{s} OTB", "{c} {u} plan vs actual", "did we hit sales budget {d}", "{k} budget variance {d}",
    "{c} {s} buy plan", "can we chase more {u}", "{d} {c} plan figure", "{s} budget utilisation",
],
"store_ranking": [
    "top {n} stores {d}", "{c} store ranking {d}", "where does {m} rank {d}", "bottom {n} stores {d}", "best stores for {c} {u}",
    "{d} store performance league table", "how is {m} performing {d}", "fastest growing stores {y} {d}", "{c} worst {n} stores {d}",
    "{m} rank in {u} sales", "{d} sales per square metre ranking", "stores ranked by revenue {d}", "did {m} hit target {d}",
],
"order_eta": [
    "when will the {c} {u} order arrive", "{s} {u} delivery date", "{c} {u} open orders", "any supplier delays on {u}",
    "{s} {c} intake date", "how much of the {u} order has arrived", "{c} {u} delivery percentage", "{c} intake {d}",
    "has the {u} ETA slipped", "{s} {u} received into the DC", "{c} {u} outstanding orders", "will the {u} repeat land in time",
    "{s} {c} order status",
],
"returns": [
    "{c} {u} return rate", "{m} returns {d}", "{c} returns units {d}", "when is the {s} returns collection", "{u} return percentage {d}",
    "is the {m} {s} return done", "{c} store returns {d}", "which stores still owe {s} returns", "{d} online return rate for {u}",
    "{c} {u} return reasons", "pending returns at {m}", "{c} stock left after {s} returns",
],
"capacity": [
    "{m} {c} capacity", "is there enough store capacity for {c} {u}", "{m} fill rate", "how many options can {m} take in {c}",
    "{m} {c} hanging capacity", "space for {u} in {m}", "{c} capacity utilisation {d}", "{m} option count plan",
    "{m} {c} {u} assortment plan", "how many units can {m} hold in {c}", "{c} stores over capacity {d}", "is {m} over capacity in {c}",
],
"out_of_scope": [
    "hi how are you", "what's the weather today", "what time is it", "thanks", "have a good day", "when is the meeting",
    "what's for lunch", "tell me a joke", "what's the dollar rate", "is tomorrow a holiday", "my laptop won't start",
    "I forgot my password", "how is traffic", "what should I do this weekend", "hello", "see you", "ok fine", "is that right",
    "can you repeat that", "help", "the printer is not working", "where is the leave form", "when is payday",
    "where is my parcel tracking number", "what time is the match", "nearest pharmacy",
],
}

LEX = {"tr": TR, "en": EN}
SLOT_KEYS = {"c": "gender", "u": "product_group", "d": "period", "k": "channel", "o": "measure", "y": "comparison", "s": "season"}


def store(L):
    r = random.random()
    if r < 0.4:
        ad = random.choice(L["store_city"]) + random.choice(L["store_suffix_a"])
    elif r < 0.8:
        ad = random.choice(L["store_district"]) + random.choice(L["store_suffix_b"])
    else:
        ad = str(random.randint(1001, 1999))
    ad = ad.strip()
    return ad, ad.upper()


def fill(template, L):
    slots, text = {}, template
    for ph, key in SLOT_KEYS.items():
        token = "{" + ph + "}"
        if token in text:
            surf = random.choice(list(L[key])); text = text.replace(token, surf); slots[key] = L[key][surf]
    while "{m}" in text:
        surf, val = store(L); text = text.replace("{m}", surf, 1); slots.setdefault("store", []).append(val)
    if "{n}" in text:
        surf = random.choice(L["n"]); text = text.replace("{n}", surf); slots["n"] = int(re.sub(r"\D", "", surf))
    if "store" in slots and len(slots["store"]) == 1:
        slots["store"] = slots["store"][0]
    is_q = re.search(L["question_end"], text.strip())
    suffix = random.choice(["", "", "?", "?"]) if is_q else random.choice(L["suffix"])
    prefix = random.choice(L["prefix"])
    if prefix.strip().lower() in ("lütfen", "please") and ("lütfen" in suffix or "please" in suffix):
        suffix = ""
    text = prefix + text + suffix
    r = random.random()
    if r < 0.25:
        text = text.lower()
    elif r < 0.35:
        text = text[0].upper() + text[1:]
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+\?", "?", text)
    return text, slots


def generate(lang, seed, per_intent=150, oos=60):
    random.seed(seed)
    L = LEX[lang]; T = L["templates"]
    test_tpl = {}
    for intent, tpls in T.items():
        s = tpls[:]; random.shuffle(s)
        test_tpl[intent] = set(s[: max(1, round(len(s) * 0.2))]) if intent != "out_of_scope" else set()
    rows, seen = [], set()
    for intent, tpls in T.items():
        target = oos if intent == "out_of_scope" else per_intent
        n = tries = 0
        while n < target and tries < target * 30:
            tries += 1
            tpl = random.choice(tpls)
            if intent == "out_of_scope":
                text = random.choice(["", "", "", L["prefix"][4], L["prefix"][5]]) + tpl + random.choice(["", "", "?", "!", "."])
                text = re.sub(r"\s+\?", "?", text).strip(); slots = {}
                if random.random() < 0.3: text = text.lower()
                elif random.random() < 0.5: text = text[0].upper() + text[1:]
            else:
                text, slots = fill(tpl, L)
            key = text.lower()
            if key in seen: continue
            seen.add(key); n += 1
            rows.append({"id": f"{lang}-" + hashlib.md5(key.encode()).hexdigest()[:10], "text": text, "intent": intent,
                         "slots": slots, "lang": lang, "_split": "test" if tpl in test_tpl[intent] else "train"})
    random.shuffle(rows)
    train = [r for r in rows if r["_split"] == "train"]; test = [r for r in rows if r["_split"] == "test"]
    oos_rows = [r for r in train if r["intent"] == "out_of_scope"]; random.shuffle(oos_rows)
    for r in oos_rows[: round(len(oos_rows) * 0.15)]:
        train.remove(r); test.append(r)
    return train, test, {i: len(t) for i, t in T.items()}


def main():
    schema = {"version": "0.2", "languages": ["tr", "en"], "intents": sorted(TR["templates"]), "slots": {}, "splits": {},
              "split_method": "template-level holdout: test templates never appear in train", "templates": {}}
    for key in ["gender", "product_group", "period", "channel", "measure", "comparison", "season"]:
        schema["slots"][key] = sorted(set(TR[key].values()) | set(EN[key].values()))
    schema["slots"]["store"] = "free text (city / district name or 4-digit code), list if more than one"
    schema["slots"]["n"] = "integer (top-N)"
    assert set(TR["templates"]) == set(EN["templates"]), "intent sets differ"
    for lang, seed in (("tr", 20261115), ("en", 20261116)):
        train, test, tcount = generate(lang, seed)
        d = OUT / lang; d.mkdir(parents=True, exist_ok=True)
        for name, rows in (("train", train), ("test", test)):
            with open(d / f"{name}.jsonl", "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps({k: v for k, v in r.items() if k != "_split"}, ensure_ascii=False) + "\n")
        schema["splits"][lang] = {"train": len(train), "test": len(test)}
        schema["templates"][lang] = tcount
        print(f"{lang}: train {len(train)} · test {len(test)}")
        for r in random.sample(train, 4): print("  ", r["intent"], "|", r["text"], "|", r["slots"])
    (OUT / "schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
