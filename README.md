# ⚽ Maçkolik İstatistik Toplayıcı

Maçkolik.com'dan tüm futbol istatistiklerini profesyonel şekilde çeken Python uygulaması.

## Özellikler

- **Puan Durumu**: Tüm liglerin güncel puan tabloları
- **Gol Krallığı**: En çok gol atan oyuncular
- **Asist Sıralaması**: En çok asist yapan oyuncular
- **Kart İstatistikleri**: Sarı ve kırmızı kart sıralamaları
- **Maç Sonuçları**: Oynanan maçların sonuçları
- **Fikstür**: Yaklaşan maçlar
- **Takım İstatistikleri**: Detaylı takım performans verileri
- **Canlı Skorlar**: Anlık maç sonuçları
- **Çoklu Lig Desteği**: Süper Lig, Premier Lig, La Liga, Bundesliga, Serie A, Ligue 1, Şampiyonlar Ligi
- **Çoklu Format**: JSON, CSV, Excel dışa aktarma
- **Zengin Terminal Arayüzü**: Renkli tablolar ve ilerleme göstergeleri

## Desteklenen Ligler

| Kısaltma | Lig |
|---|---|
| `super-lig` | Türkiye Süper Lig |
| `1-lig` | Türkiye 1. Lig |
| `premier-league` | İngiltere Premier Lig |
| `la-liga` | İspanya La Liga |
| `bundesliga` | Almanya Bundesliga |
| `serie-a` | İtalya Serie A |
| `ligue-1` | Fransa Ligue 1 |
| `champions-league` | UEFA Şampiyonlar Ligi |

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

### Tek Lig - Tüm İstatistikler
```bash
python main.py --league super-lig --all
```

### Belirli İstatistikler
```bash
# Puan durumu
python main.py -l super-lig --standings

# Gol krallığı + Asistler
python main.py -l premier-league --scorers --assists

# Sarı ve kırmızı kartlar
python main.py -l la-liga --yellow-cards --red-cards

# Maç sonuçları
python main.py -l bundesliga --matches

# Takım istatistikleri
python main.py -l serie-a --team-stats
```

### Canlı Skorlar
```bash
python main.py --live
```

### Bugünkü Maçlar
```bash
python main.py --today
```

### Tüm Ligler
```bash
python main.py --all-leagues --all
```

### Dışa Aktarma
```bash
# JSON formatında
python main.py -l super-lig --all --format json

# CSV formatında
python main.py -l super-lig --all --format csv

# Excel formatında (stil ve renk ile)
python main.py -l super-lig --all --format excel

# Tüm formatlarda
python main.py -l super-lig --all --format all

# Özel çıktı klasörü
python main.py -l super-lig --all --format excel --output veriler/
```

## Proje Yapısı

```
ma-kolik/
├── main.py                          # CLI giriş noktası
├── requirements.txt                 # Bağımlılıklar
├── setup.py                         # Kurulum
├── mackolik/
│   ├── __init__.py
│   ├── config.py                    # Yapılandırma (URL, lig bilgileri)
│   ├── scraper.py                   # HTTP istemcisi (rate limiting, retry)
│   ├── models/
│   │   └── __init__.py              # Veri modelleri (Team, Player, Match)
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── standings.py             # Puan durumu
│   │   ├── matches.py               # Maç sonuçları ve fikstür
│   │   ├── player_stats.py          # Oyuncu istatistikleri
│   │   ├── team_stats.py            # Takım istatistikleri
│   │   └── live_scores.py           # Canlı skorlar
│   └── exporters/
│       ├── __init__.py
│       └── exporter.py              # JSON, CSV, Excel dışa aktarma
└── output/                          # Dışa aktarılan veriler
```

## CLI Seçenekleri

| Seçenek | Kısa | Açıklama |
|---|---|---|
| `--league` | `-l` | Lig seçimi |
| `--all-leagues` | | Tüm ligler |
| `--standings` | `-s` | Puan durumu |
| `--scorers` | `-g` | Gol krallığı |
| `--assists` | `-a` | Asist sıralaması |
| `--yellow-cards` | `-y` | Sarı kartlar |
| `--red-cards` | `-r` | Kırmızı kartlar |
| `--matches` | `-m` | Maç sonuçları |
| `--team-stats` | `-t` | Takım istatistikleri |
| `--live` | | Canlı skorlar |
| `--today` | | Bugünkü maçlar |
| `--all` | | Tüm istatistikler |
| `--format` | `-f` | Çıktı formatı (json/csv/excel/all) |
| `--output` | `-o` | Çıktı klasörü |
| `--verbose` | `-v` | Detaylı log |
