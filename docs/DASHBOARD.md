# 🎛️ Gotowy Dashboard i Karta Sterowania (100% Native Home Assistant)

Wielu użytkowników pomp ciepła spotyka się z problemem niewygodnego sterowania w Home Assistant: koniecznością szukania encji na liście, otwierania okna dialogowego i mozolnego wpisywania wartości z klawiatury (np. z 29 na 30°C) lub przesuwania suwaka.

W tym katalogu znajdziesz **gotowe, zoptymalizowane rozwiązania oparte w 100% na natywnym interfejsie Home Assistant** – bez potrzeby instalowania jakichkolwiek zewnętrznych kart z HACS!

---

## 🚀 Jak to działa? Natywne przyciski `+` i `-` w HA

Od wersji Home Assistant 2023.12+ standardowa karta **Kafelek (`tile`)** posiada wbudowaną obsługę funkcji `numeric-input` ze stylem `buttons`. 

Gdy skonfigurujesz encję typu `number` w ten sposób:
```yaml
type: tile
entity: number.heat_pump_heating_setpoint
name: Zadana CO (P01)
features:
  - type: numeric-input
    style: buttons
```
Home Assistant automatycznie wyświetla na kafelku duże, interaktywne przyciski **`[-]`** oraz **`[+]`**. Każde kliknięcie natychmiast zmienia zadaną temperaturę lub histerezę o dokładnie zdefiniowany krok (np. `0.5°C` dla temperatur lub `1.0°C` dla histerezy)!

---

## 📦 Dwa warianty do wyboru

W repozytorium przygotowaliśmy dwa gotowe pliki konfiguracyjne YAML:

1. **[Kompaktowa Karta Zarządzania (Management Card)](../dashboards/sprsun_control_card.yaml)**  
   Idealna do wklejenia na Twój istniejący pulpit (np. na stronę główną obok innych urządzeń). Łączy sterowanie zasilaniem, trybem jednostki, nastawami CO/CWU z przyciskami `+`/`-`, kluczowymi temperaturami oraz statusem podzespołów w jeden estetyczny blok pionowy.

2. **[Pełny Pulpit Pompy Ciepła (Full Dashboard View)](../dashboards/sprsun_full_dashboard.yaml)**  
   Kompletny widok / osobna zakładka zorganizowana w czytelne sekcje:
   - ⚡ **Sterowanie szybkie** (Zasilanie, Tryby, CO, CWU, Chłodzenie z przyciskami +/-)
   - 🌡️ **Monitoring temperatur i przepływu** (Zasilanie, powrót, zbiornik CWU, temp. zewnętrzna, parownik, skraplacz, gaz ssawny i tłoczenie)
   - ⚡ **Energia, moc i COP** (Moc grzewcza, COP, napięcia, prądy, częstotliwość inwertera, czas pracy sprężarki)
   - ⚙️ **Stan przekaźników i zapotrzebowania** (Sprężarka, wentylator, pompa obiegowa, zawory 3- i 4-drogowe, odszranianie)
   - 🛡️ **Antylegionella i opcje zaawansowane** (Harmonogram wygrzewania zasobnika, tryb pompy G02, reset błędów)

---

## 🛠️ Instrukcja instalacji krok po kroku

### Wariant A: Dodanie Kompaktowej Karty do istniejącego pulpitu

1. Otwórz plik [`dashboards/sprsun_control_card.yaml`](../dashboards/sprsun_control_card.yaml) i skopiuj jego zawartość.
2. W Home Assistant przejdź do swojego pulpitu (Dashboard).
3. Kliknij ikonę **ołówka** w prawym górnym rogu (**Edytuj pulpit**).
4. Kliknij przycisk **+ Dodaj kartę** (na dole ekranu).
5. Zjedź na sam dół listy i wybierz **Ręczna karta** (Manual).
6. Wklej skopiowany kod YAML.
7. **Dopasowanie nazw encji (jeśli dotyczy):**  
   Domyślny kod używa prefiksu `heat_pump` (np. `number.heat_pump_heating_setpoint`).  
   Jeśli podczas dodawania integracji nazwałeś pompę np. *„Pompa Ciepła”* lub *„SPRSUN”*, użyj skrótu **Ctrl+F** w edytorze i zamień `heat_pump` na swój prefiks (np. `pompa_ciepla`).
8. Kliknij **Zapisz**. Gotowe!

---

### Wariant B: Dodanie Pełnego Pulpitu jako nowej zakładki

1. Otwórz plik [`dashboards/sprsun_full_dashboard.yaml`](../dashboards/sprsun_full_dashboard.yaml) i skopiuj jego zawartość.
2. W Home Assistant przejdź do swojego pulpitu i kliknij **Edytuj pulpit**.
3. Na górnym pasku zakładek kliknij ikonę **+** (Dodaj widok).
4. W oknie konfiguracji nowego widoku kliknij trzy kropki (⋮) w prawym górnym rogu i wybierz **Edytor konfiguracji RAW** (lub przełącz edytor karty na YAML).
5. Wklej konfigurację widoku i kliknij **Zapisz**.

---

## 📋 Tabela mapowania kontrolek na parametry SPRSUN

| Element interfejsu | Parametr | Encja w Home Assistant | Krok zmiany |
| :--- | :---: | :--- | :---: |
| **Zadana CO** | **P01** | `number.heat_pump_heating_setpoint` | `0.5°C` (przyciski +/-) |
| **Histereza CO** | **P03** | `number.heat_pump_heating_cooling_temp_diff` | `1.0°C` (przyciski +/-) |
| **Zadana CWU** | **P04** | `number.heat_pump_hot_water_setpoint` | `0.5°C` (przyciski +/-) |
| **Histereza CWU** | **P05** | `number.heat_pump_hot_water_temp_diff` | `1.0°C` (przyciski +/-) |
| **Zadana Chłodzenia**| **P02** | `number.heat_pump_cooling_setpoint` | `0.5°C` (przyciski +/-) |
| **Zasilanie pompy** | - | `switch.heat_pump_power` | Włącz / Wyłącz |
| **Tryb jednostki** | **P06** | `select.heat_pump_unit_mode` | CO / CWU / CO+CWU itp. |
| **Tryb wentylatora** | **P07** | `select.heat_pump_fan_mode` | Normal / Eco / Night / Test |
| **Tryb pompy obiegowej**| **G02**| `select.heat_pump_pump_work_mode` | Interwał / Normal / Demand |
| **Reset błędów** | - | `button.heat_pump_failure_reset` | Przycisk resetujący awarię |

---

## 💡 Automatyczne powiadamianie o błędach (Karta warunkowa)

Oba szablony zawierają kartę warunkową (`type: conditional`):
- W stanie normalnym (brak awarii) karta pozostaje całkowicie ukryta i nie zabiera miejsca.
- Jeśli pompa zgłosi stan awaryjny (`binary_sensor.heat_pump_alarm_stop` przejdzie w stan `on`), na samej górze dashboardu pojawi się **czerwony kafelek alarmowy z bezpośrednim przyciskiem do zresetowania błędu** (`button.heat_pump_failure_reset`).
