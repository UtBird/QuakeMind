PROVINCES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya",
    "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu",
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır",
    "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun",
    "Gümüşhane", "Hakkâri", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir",
    "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya",
    "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş",
    "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop",
    "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", "Uşak",
    "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kırıkkale",
    "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük",
    "Kilis", "Osmaniye", "Düzce",
]

PROVINCE_TO_DISTRICTS = {
    "İstanbul": [
        "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler",
        "Bakırköy", "Başakşehir", "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü",
        "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy", "Esenler", "Esenyurt",
        "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane",
        "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer",
        "Silivri", "Sultanbeyli", "Sultangazi", "Şile", "Şişli", "Tuzla",
        "Ümraniye", "Üsküdar", "Zeytinburnu",
    ],
    "Ankara": [
        "Altındağ", "Çankaya", "Etimesgut", "Gölbaşı", "Keçiören", "Mamak",
        "Pursaklar", "Sincan", "Yenimahalle", "Akyurt", "Beypazarı", "Polatlı",
    ],
    "İzmir": [
        "Bornova", "Buca", "Çeşme", "Foça", "Karabağlar", "Karşıyaka", "Konak",
        "Menemen", "Torbalı", "Aliağa", "Balçova",
    ],
    "Hatay": [
        "Antakya", "Arsuz", "Belen", "Defne", "Dörtyol", "Erzin", "Hassa",
        "İskenderun", "Kırıkhan", "Kumlu", "Payas", "Reyhanlı", "Samandağ",
        "Yayladağı", "Altınözü",
    ],
    "Gaziantep": [
        "Nurdağı", "İslahiye", "Şahinbey", "Şehitkamil", "Nizip", "Oğuzeli",
        "Yavuzeli", "Araban", "Karkamış",
    ],
    "Kahramanmaraş": [
        "Elbistan", "Pazarcık", "Afşin", "Dulkadiroğlu", "Onikişubat", "Türkoğlu",
        "Göksun", "Çağlayancerit", "Ekinözü", "Andırın",
    ],
    "Malatya": [
        "Doğanşehir", "Yeşilyurt", "Battalgazi", "Akçadağ", "Darende",
        "Doğanyol", "Hekimhan", "Kale", "Kuluncak", "Pütürge", "Yazıhan",
    ],
    "Adıyaman": [
        "Besni", "Gölbaşı", "Kahta", "Samsat", "Tut", "Gerger", "Çelikhan",
    ],
    "Adana": [
        "Ceyhan", "Çukurova", "İmamoğlu", "Karaisalı", "Karataş", "Kozan",
        "Pozantı", "Saimbeyli", "Sarıçam", "Seyhan", "Tufanbeyli", "Yumurtalık",
        "Yüreğir",
    ],
    "Osmaniye": [
        "Kadirli", "Düziçi", "Bahçe", "Hasanbeyli", "Sumbas", "Toprakkale",
    ],
    "Diyarbakır": [
        "Bismil", "Ergani", "Kayapınar", "Sur", "Yenişehir", "Bağlar",
    ],
    "Şanlıurfa": [
        "Siverek", "Viranşehir", "Haliliye", "Karaköprü", "Eyyübiye", "Akçakale",
        "Birecik", "Ceylanpınar", "Suruç",
    ],
    "Kilis": [
        "Elbeyli", "Musabeyli", "Polateli",
    ],
}

# J-13 duzeltmesi: il/ilce merkezlerinin yaklasik (WGS84) koordinatlari --
# offline modda ya da Nominatim'e gitmeden ONCE denenen yerel bir sozluk.
# Il merkezi/ilce merkezi hassasiyetinde (birkac km) -- sokak duzeyinde degil;
# amac afet mudahalesinde "hangi bolge" sorusuna aninda, ag gerektirmeden
# cevap verebilmek (bkz. ner_extraction.py::_local_geocode).
PROVINCE_COORDS = {
    "Adana": (37.0000, 35.3213), "Adıyaman": (37.7648, 38.2786),
    "Afyonkarahisar": (38.7507, 30.5567), "Ağrı": (39.7191, 43.0503),
    "Amasya": (40.6499, 35.8353), "Ankara": (39.9334, 32.8597),
    "Antalya": (36.8969, 30.7133), "Artvin": (41.1828, 41.8183),
    "Aydın": (37.8560, 27.8416), "Balıkesir": (39.6484, 27.8826),
    "Bilecik": (40.1506, 29.9792), "Bingöl": (38.8855, 40.4966),
    "Bitlis": (38.4006, 42.1095), "Bolu": (40.7397, 31.6110),
    "Burdur": (37.7203, 30.2908), "Bursa": (40.1826, 29.0665),
    "Çanakkale": (40.1553, 26.4142), "Çankırı": (40.6013, 33.6134),
    "Çorum": (40.5506, 34.9556), "Denizli": (37.7765, 29.0864),
    "Diyarbakır": (37.9144, 40.2306), "Edirne": (41.6771, 26.5557),
    "Elazığ": (38.6810, 39.2264), "Erzincan": (39.7500, 39.4923),
    "Erzurum": (39.9000, 41.2700), "Eskişehir": (39.7767, 30.5206),
    "Gaziantep": (37.0662, 37.3833), "Giresun": (40.9128, 38.3895),
    "Gümüşhane": (40.4386, 39.5086), "Hakkâri": (37.5744, 43.7408),
    "Hatay": (36.4018, 36.3498), "Isparta": (37.7648, 30.5566),
    "Mersin": (36.8000, 34.6333), "İstanbul": (41.0082, 28.9784),
    "İzmir": (38.4192, 27.1287), "Kars": (40.6167, 43.1000),
    "Kastamonu": (41.3887, 33.7827), "Kayseri": (38.7312, 35.4787),
    "Kırklareli": (41.7333, 27.2167), "Kırşehir": (39.1425, 34.1709),
    "Kocaeli": (40.8533, 29.8815), "Konya": (37.8746, 32.4932),
    "Kütahya": (39.4242, 29.9833), "Malatya": (38.3552, 38.3095),
    "Manisa": (38.6191, 27.4289), "Kahramanmaraş": (37.5753, 36.9228),
    "Mardin": (37.3212, 40.7245), "Muğla": (37.2153, 28.3636),
    "Muş": (38.9462, 41.7539), "Nevşehir": (38.6244, 34.7239),
    "Niğde": (37.9667, 34.6833), "Ordu": (40.9839, 37.8764),
    "Rize": (41.0201, 40.5234), "Sakarya": (40.6940, 30.4358),
    "Samsun": (41.2867, 36.3300), "Siirt": (37.9333, 41.9500),
    "Sinop": (42.0231, 35.1531), "Sivas": (39.7477, 37.0179),
    "Tekirdağ": (40.9833, 27.5167), "Tokat": (40.3167, 36.5500),
    "Trabzon": (41.0027, 39.7168), "Tunceli": (39.1079, 39.5401),
    "Şanlıurfa": (37.1591, 38.7969), "Uşak": (38.6823, 29.4082),
    "Van": (38.4891, 43.4089), "Yozgat": (39.8181, 34.8147),
    "Zonguldak": (41.4564, 31.7987), "Aksaray": (38.3687, 34.0360),
    "Bayburt": (40.2552, 40.2249), "Karaman": (37.1759, 33.2287),
    "Kırıkkale": (39.8468, 33.5153), "Batman": (37.8812, 41.1351),
    "Şırnak": (37.4187, 42.4918), "Bartın": (41.6344, 32.3375),
    "Ardahan": (41.1105, 42.7022), "Iğdır": (39.9167, 44.0333),
    "Yalova": (40.6500, 29.2667), "Karabük": (41.2061, 32.6204),
    "Kilis": (36.7184, 37.1212), "Osmaniye": (37.0742, 36.2478),
    "Düzce": (40.8438, 31.1565),
}

# (il, ilce) -> (lat, lon). Yalniz PROVINCE_TO_DISTRICTS'te listelenen
# (afet mudahalesi/deprem bolgesi agirlikli) illerin ilceleri icin.
DISTRICT_COORDS = {
    ("İstanbul", "Adalar"): (40.8767, 29.0913), ("İstanbul", "Arnavutköy"): (41.1874, 28.7406),
    ("İstanbul", "Ataşehir"): (40.9923, 29.1244), ("İstanbul", "Avcılar"): (40.9793, 28.7215),
    ("İstanbul", "Bağcılar"): (41.0344, 28.8564), ("İstanbul", "Bahçelievler"): (41.0021, 28.8600),
    ("İstanbul", "Bakırköy"): (40.9819, 28.8772), ("İstanbul", "Başakşehir"): (41.0949, 28.8017),
    ("İstanbul", "Bayrampaşa"): (41.0472, 28.9153), ("İstanbul", "Beşiktaş"): (41.0422, 29.0083),
    ("İstanbul", "Beykoz"): (41.1358, 29.0956), ("İstanbul", "Beylikdüzü"): (41.0019, 28.6414),
    ("İstanbul", "Beyoğlu"): (41.0369, 28.9772), ("İstanbul", "Büyükçekmece"): (41.0208, 28.5942),
    ("İstanbul", "Çatalca"): (41.1436, 28.4636), ("İstanbul", "Çekmeköy"): (41.0356, 29.1858),
    ("İstanbul", "Esenler"): (41.0447, 28.8797), ("İstanbul", "Esenyurt"): (41.0347, 28.6764),
    ("İstanbul", "Eyüpsultan"): (41.0483, 28.9339), ("İstanbul", "Fatih"): (41.0186, 28.9497),
    ("İstanbul", "Gaziosmanpaşa"): (41.0575, 28.9153), ("İstanbul", "Güngören"): (41.0186, 28.8747),
    ("İstanbul", "Kadıköy"): (40.9819, 29.0272), ("İstanbul", "Kağıthane"): (41.0794, 28.9736),
    ("İstanbul", "Kartal"): (40.8964, 29.1908), ("İstanbul", "Küçükçekmece"): (41.0000, 28.7750),
    ("İstanbul", "Maltepe"): (40.9350, 29.1508), ("İstanbul", "Pendik"): (40.8778, 29.2497),
    ("İstanbul", "Sancaktepe"): (41.0011, 29.2358), ("İstanbul", "Sarıyer"): (41.1672, 29.0575),
    ("İstanbul", "Silivri"): (41.0736, 28.2467), ("İstanbul", "Sultanbeyli"): (40.9686, 29.2653),
    ("İstanbul", "Sultangazi"): (41.1067, 28.8672), ("İstanbul", "Şile"): (41.1753, 29.6136),
    ("İstanbul", "Şişli"): (41.0603, 28.9878), ("İstanbul", "Tuzla"): (40.8158, 29.3033),
    ("İstanbul", "Ümraniye"): (41.0161, 29.1244), ("İstanbul", "Üsküdar"): (41.0225, 29.0144),
    ("İstanbul", "Zeytinburnu"): (40.9942, 28.9017),

    ("Ankara", "Altındağ"): (39.9639, 32.8642), ("Ankara", "Çankaya"): (39.9078, 32.8622),
    ("Ankara", "Etimesgut"): (39.9469, 32.6689), ("Ankara", "Gölbaşı"): (39.7906, 32.8058),
    ("Ankara", "Keçiören"): (39.9825, 32.8642), ("Ankara", "Mamak"): (39.9308, 32.9047),
    ("Ankara", "Pursaklar"): (40.0431, 32.8908), ("Ankara", "Sincan"): (39.9647, 32.5772),
    ("Ankara", "Yenimahalle"): (39.9700, 32.7947), ("Ankara", "Akyurt"): (40.1333, 33.0833),
    ("Ankara", "Beypazarı"): (40.1667, 31.9167), ("Ankara", "Polatlı"): (39.5806, 32.1470),

    ("İzmir", "Bornova"): (38.4667, 27.2167), ("İzmir", "Buca"): (38.3667, 27.1667),
    ("İzmir", "Çeşme"): (38.3236, 26.3033), ("İzmir", "Foça"): (38.6667, 26.7500),
    ("İzmir", "Karabağlar"): (38.3833, 27.1333), ("İzmir", "Karşıyaka"): (38.4611, 27.1097),
    ("İzmir", "Konak"): (38.4189, 27.1287), ("İzmir", "Menemen"): (38.6111, 27.0664),
    ("İzmir", "Torbalı"): (38.1600, 27.3600), ("İzmir", "Aliağa"): (38.7986, 26.9719),
    ("İzmir", "Balçova"): (38.3833, 27.0500),

    ("Hatay", "Antakya"): (36.2028, 36.1600), ("Hatay", "Arsuz"): (36.3872, 35.8853),
    ("Hatay", "Belen"): (36.2400, 36.1900), ("Hatay", "Defne"): (36.1700, 36.1300),
    ("Hatay", "Dörtyol"): (36.8460, 36.2270), ("Hatay", "Erzin"): (36.9556, 36.2000),
    ("Hatay", "Hassa"): (36.7942, 36.5231), ("Hatay", "İskenderun"): (36.5875, 36.1739),
    ("Hatay", "Kırıkhan"): (36.5039, 36.3494), ("Hatay", "Kumlu"): (36.4300, 36.3200),
    ("Hatay", "Payas"): (36.7600, 36.2000), ("Hatay", "Reyhanlı"): (36.2667, 36.5667),
    ("Hatay", "Samandağ"): (36.0833, 35.9833), ("Hatay", "Yayladağı"): (35.9200, 36.0300),
    ("Hatay", "Altınözü"): (36.1300, 36.2700),

    ("Gaziantep", "Nurdağı"): (37.1833, 36.7500), ("Gaziantep", "İslahiye"): (37.0242, 36.6317),
    ("Gaziantep", "Şahinbey"): (37.0592, 37.3428), ("Gaziantep", "Şehitkamil"): (37.1100, 37.3600),
    ("Gaziantep", "Nizip"): (37.0117, 37.7981), ("Gaziantep", "Oğuzeli"): (36.9333, 37.5333),
    ("Gaziantep", "Yavuzeli"): (37.2333, 37.6667), ("Gaziantep", "Araban"): (37.3667, 37.6833),
    ("Gaziantep", "Karkamış"): (36.8167, 38.0167),

    ("Kahramanmaraş", "Elbistan"): (38.2019, 37.1972), ("Kahramanmaraş", "Pazarcık"): (37.4956, 37.2986),
    ("Kahramanmaraş", "Afşin"): (38.2489, 36.9111), ("Kahramanmaraş", "Dulkadiroğlu"): (37.5900, 36.9500),
    ("Kahramanmaraş", "Onikişubat"): (37.5833, 36.9167), ("Kahramanmaraş", "Türkoğlu"): (37.3833, 36.8833),
    ("Kahramanmaraş", "Göksun"): (38.0333, 36.5000), ("Kahramanmaraş", "Çağlayancerit"): (37.5333, 36.6167),
    ("Kahramanmaraş", "Ekinözü"): (38.1000, 36.9333), ("Kahramanmaraş", "Andırın"): (37.9333, 36.3500),

    ("Malatya", "Doğanşehir"): (38.0961, 37.8814), ("Malatya", "Yeşilyurt"): (38.3400, 38.2500),
    ("Malatya", "Battalgazi"): (38.3667, 38.3833), ("Malatya", "Akçadağ"): (38.3389, 37.9631),
    ("Malatya", "Darende"): (38.5883, 37.5061), ("Malatya", "Doğanyol"): (38.2400, 39.1500),
    ("Malatya", "Hekimhan"): (38.8236, 37.9264), ("Malatya", "Kale"): (38.4167, 39.1667),
    ("Malatya", "Kuluncak"): (38.5833, 37.7167), ("Malatya", "Pütürge"): (38.2019, 38.8797),
    ("Malatya", "Yazıhan"): (38.5722, 38.2144),

    ("Adıyaman", "Besni"): (37.6919, 37.8567), ("Adıyaman", "Gölbaşı"): (37.7833, 37.6333),
    ("Adıyaman", "Kahta"): (37.7833, 38.6167), ("Adıyaman", "Samsat"): (37.5808, 38.9564),
    ("Adıyaman", "Tut"): (37.8956, 38.2400), ("Adıyaman", "Gerger"): (38.2686, 39.1128),
    ("Adıyaman", "Çelikhan"): (38.1667, 38.8500),

    ("Adana", "Ceyhan"): (37.0256, 35.8169), ("Adana", "Çukurova"): (36.9833, 35.2667),
    ("Adana", "İmamoğlu"): (37.2667, 35.6500), ("Adana", "Karaisalı"): (37.2667, 35.0167),
    ("Adana", "Karataş"): (36.5667, 35.3667), ("Adana", "Kozan"): (37.4508, 35.8156),
    ("Adana", "Pozantı"): (37.4231, 34.8664), ("Adana", "Saimbeyli"): (38.0989, 36.0800),
    ("Adana", "Sarıçam"): (37.0333, 35.3833), ("Adana", "Seyhan"): (37.0000, 35.3167),
    ("Adana", "Tufanbeyli"): (38.2667, 36.2167), ("Adana", "Yumurtalık"): (36.7681, 35.7900),
    ("Adana", "Yüreğir"): (36.9833, 35.3667),

    ("Osmaniye", "Kadirli"): (37.3719, 36.0958), ("Osmaniye", "Düziçi"): (37.4167, 36.3667),
    ("Osmaniye", "Bahçe"): (37.2000, 36.5667), ("Osmaniye", "Hasanbeyli"): (37.3833, 36.4667),
    ("Osmaniye", "Sumbas"): (37.3667, 36.1833), ("Osmaniye", "Toprakkale"): (37.0833, 36.1667),

    ("Diyarbakır", "Bismil"): (37.8500, 40.6667), ("Diyarbakır", "Ergani"): (38.2667, 39.7667),
    ("Diyarbakır", "Kayapınar"): (37.9167, 40.1833), ("Diyarbakır", "Sur"): (37.9083, 40.2394),
    ("Diyarbakır", "Yenişehir"): (37.9161, 40.2242), ("Diyarbakır", "Bağlar"): (37.9200, 40.2200),

    ("Şanlıurfa", "Siverek"): (37.7550, 39.3150), ("Şanlıurfa", "Viranşehir"): (37.2372, 39.7644),
    ("Şanlıurfa", "Haliliye"): (37.1594, 38.7756), ("Şanlıurfa", "Karaköprü"): (37.2000, 38.7833),
    ("Şanlıurfa", "Eyyübiye"): (37.1500, 38.8000), ("Şanlıurfa", "Akçakale"): (36.7167, 38.9500),
    ("Şanlıurfa", "Birecik"): (37.0333, 37.9833), ("Şanlıurfa", "Ceylanpınar"): (36.8500, 40.0500),
    ("Şanlıurfa", "Suruç"): (36.9667, 38.4333),

    ("Kilis", "Elbeyli"): (36.8500, 37.5333), ("Kilis", "Musabeyli"): (36.9333, 37.0667),
    ("Kilis", "Polateli"): (36.6667, 37.3833),
}
