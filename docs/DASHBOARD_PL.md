# 🎛️ Wbudowane Dashboardy Home Assistant (100% Natywny Lovelace)

*[English guide available here: DASHBOARD.md](DASHBOARD.md)*

Integracja zawiera wbudowane, w **100% natywne strategie Lovelace** dla Home Assistanta (układ **Sekcji** — **bez instalowania kart z HACS i bez ręcznego kopiowania YAML-a**).

- **Automatyczny język:** Dashboard sam dobiera język (`pl`, `en`, `fr`, `de`, `es`, `cs`, `sk`, `hu`, `lt`, `uk`) na podstawie ustawień Twojego profilu w HA z jednego wspólnego szablonu i słownika tłumaczeń.
- **Automatyczne wykrywanie encji:** Sam znajduje rzeczywiste `entity_id` po `unique_id` — działa od razu nawet po zmianie nazwy pompy (bez żadnego `Ctrl+H`).
- **Możliwość pełnej edycji:** W dowolnym momencie możesz kliknąć **Przejmij kontrolę** w HA, aby zamienić pulpit w zwykły edytowalny dashboard.

---

## 📦 Zawartość

| Element | Opis |
| :--- | :--- |
| **Wbudowany Dashboard (`custom:sprsun`)** | Pełny **4-zakładkowy Dashboard** (`Domyślny`, `Szczegółowy`, `Diagnostyczny`, `Optymalizacyjny`) dostępny bezpośrednio w **+ Dodaj pulpit** |
| **Wbudowana Sekcja Sterowania (`custom:sprsun-control`)** | Kompaktowa sekcja sterowania dostępna z **+ Dodaj sekcję** na dowolnym pulpicie |
| **[dashboards/sprsun_optimization_helpers.yaml](../dashboards/sprsun_optimization_helpers.yaml)** | Opcjonalny pakiet `history_stats` + `template` (liczba defrostów 24h, czas defrostu, starty sprężarki, czas grzałek) |

### Do czego służy każda z 4 zakładek?

1. **Domyślny (`domyslny`)**: Codzienna obsługa dla każdego domownika — włącznik główny, tryb pracy (`P06`), profil hałasu (`P07`), przyciski **`[-]` / `[+]`** dla CO/CWU/chłodzenia, termostaty, alert awarii oraz opis słowny co w tym momencie robi pompa.
2. **Szczegółowy (`szczegolowy`)**: Obieg wody i `Delta T`, pełna krzywa pogodowa ECO (`E01–E24`) porównana na żywo z rzeczywistą temperaturą wody, parametry sprężarki/wentylatora/EEV/ciśnień, Antylegionella, auto-przełączanie Lato/Zima oraz wykresy 24h.
3. **Diagnostyczny (`diagnostyczny`)**: Automatyczne centrum `24` błędów z prostą listą kontrolną *"co sprawdzić przed resetem"*, kondycja wymiennika i zaworu EEV (`Approach skraplacza`, `Przegrzanie ssania/tłoczenia`, `Temp. tłoczenia`), stany wszystkich przekaźników i wejść oraz wersje firmware.
4. **Optymalizacyjny (`optymalizacyjny`)**: **Asystent Optymalizacji na żywo** (automatyczna ocena taktowania, `Delty T`, grzałek elektrycznych `COP=1`, odchyłki od krzywej ECO, przyrostu szronu `Zewn. - Lamele` oraz czasu/odstępu defrostu) wraz z bezpiecznymi nastawami `P`/`G` i ukrytą domyślnie strefą `[EKSPERT]` do strojenia **czasu i częstotliwości defrostu (`H01–H18`, `A43`, `A51`)**, pompy DC (`F13–F17`), krzywych Hz (`R04–R45`) i harmonogramów `Timeband`.

---

## 🛠️ Instrukcja instalacji krok po kroku

### 1. Włącz „Sensory wyliczane” (Zalecane)
Aby zakładki `Szczegółowy`, `Diagnostyczny` i `Optymalizacyjny` pokazywały wszystkie wskaźniki (`Stan pracy`, `Delta T wody`, `Różnica Zewn. - Lamele`, `Odstęp defrostu`, `Cel z krzywej ECO`, `Szacowana moc`):
1. Wejdź w **Ustawienia → Urządzenia i usługi → SPRSUN Heat Pump (Modbus)**.
2. Kliknij **Konfiguruj**.
3. Zaznacz **Włącz sensory wyliczane (obliczeniowe)** i zapisz (integracja przeładuje się automatycznie).

> **Wskazówka dot. sekcji `[EKSPERT]`:** Opcję **Włącz ustawienia eksperckie** zostaw wyłączoną, dopóki nie zechcesz korygować parametrów fabrycznych (`H01–H18`, `F`, `R`). Dopóki opcja jest wyłączona, sekcje eksperckie na dashboardzie ukrywają się automatycznie.

### 2. Dodaj wbudowany 4-zakładkowy Dashboard (bez kopiowania YAML-a)
1. W Home Assistant przejdź do **Ustawienia → Pulpity → + Dodaj pulpit**.
2. Wybierz z listy strategii **Pompa Ciepła SPRSUN** (jeśli po aktualizacji integracji przeglądarka trzyma stary cache, odśwież raz przez `Ctrl+F5`).
3. *(Alternatywa YAML)* Możesz też utworzyć pusty pulpit, otworzyć **Edytor konfiguracji RAW** i wkleić:
   ```yaml
   strategy:
     type: custom:sprsun
   ```
   *(Opcjonalne pola pod `strategy:`: `entry_id` przy kilku pompach oraz `language: pl` / `en`, jeśli chcesz wymusić język inny niż w profilu HA.)*

### 3. Dodaj kompaktową sekcję sterowania na istniejący pulpit
Na dowolnym pulpicie w układzie Sekcji kliknij **Edytuj → + Dodaj sekcję** i wybierz **SPRSUN — Sterowanie** (`strategy: type: custom:sprsun-control`).

### 4. (Opcjonalnie) Statystyki 24h i zewnętrzny licznik energii
- **Liczniki dobowe defrostu i taktowania:** Skopiuj zawartość [dashboards/sprsun_optimization_helpers.yaml](../dashboards/sprsun_optimization_helpers.yaml) do folderu `packages/` w HA (lub do `configuration.yaml`) i zrestartuj HA — kafelki 24h na zakładce **Optymalizacyjny** pojawią się same.
- **Zewnętrzny licznik prądu:** W części sterowników CHICO (bez fabrycznego przepływomierza/licznika na płycie, np. `Ctrl v590`) wewnętrzne `COP`, `Moc cieplna`, `Napięcie AC` i `Przepływ` pokazują `0`. Jeśli masz osobny licznik (Shelly 3EM, Tuya itp.), dodaj jego encje kW/kWh na zakładce Optymalizacyjny.

---

## 💡 Poradnik optymalizacji („Co widzę → Co zmienić?”)

### A. Obniżanie zużycia prądu (poza defrostem)

| Objaw / Metryka | Co to oznacza po ludzku | Co warto skorygować |
| :--- | :--- | :--- |
| **Woda vs Krzywa ECO** jest wysoka lub w domu jest za ciepło | Każdy **1°C** niżej na zasilaniu CO to ok. **2–3% niższy rachunek** | Obniż `P01` (lub obniż punkty krzywej `E13–E16` o 1–2°C) |
| **Czas cyklu sprężarki `< 15 min`** (częste włącz/wyłącz) | Pompa taktuje — traci energię na częste rozruchy | Zwiększ histerezę CO `P03` (np. z `2°C` na `3–5°C`) i sprawdź `G03` (min. postój `5–10 min`) |
| **Zadana CWU `P04` > 50°C** | Grzanie wody powyżej 50°C mocno zbija sprawność (COP) | Ustaw `P04` na **45–48°C** i korzystaj z cotygodniowej dezynfekcji **Antylegionella** |
| **Włącza się grzałka elektryczna (`OUT4` / `OUT12`)** | Grzałka grzeje `1:1` (`COP = 1`), 3–4x drożej niż sprężarka | Obniż progi `G05`/`G07` (np. do `-12..-15°C`) i wydłuż opóźnienie `G06`/`G08` do `45–60 min` |
| **Delta T wody `< 2°C`** przy wysokich obrotach pompy DC | Pompa obiegowa marnuje prąd lub przepływ jest zbyt szybki | Ustaw `G02 = Demand` lub `Normal`, podnieś `G04` (celuj w `3–5°C` podłogówka / `5–8°C` grzejniki), ew. `[EKSPERT] F16/F17` |
| **Delta T wody `> 7.5°C`** lub **Approach skraplacza `> 6°C`** | Za słaby obieg wody podnosi ciśnienie skraplania i zużycie prądu | Wyczyść filtr siatkowy, odpowietrz układ, otwórz dławione pętle/grzejniki |
| **Praca w drogiej taryfie / brak wykorzystania PV** | Grzanie CWU w zimny wieczór kosztuje więcej niż w ciepłe południe | Użyj `Timeband 1–3` (`[EKSPERT]`) lub automatyzacji HA, by grzać CWU w południe (wyższa temp. zewn. = lepsze COP + prąd z PV) |

### B. Optymalizacja czasu i częstotliwości defrostu (`H01–H18`)

Każdy defrost odwraca obieg i **odbiera ciepło z domu**, żeby roztopić szron na jednostce zewnętrznej. Przed każdą korektą obserwuj wykres **Analiza defrostu (24h)** na zakładce Optymalizacyjny i zmieniaj **tylko 1 parametr naraz o mały krok**:

| Objaw na wykresie / przy pompie | Co się dzieje | Bezpieczna korekta (`[EKSPERT]`) |
| :--- | :--- | :--- |
| **Defrost wchodzi co 45–60 min**, choć `Zewn. - Lamele` było małe (`< 7–8°C`) a lamel niemal czysty | Zbyt krótki minimalny odstęp `H08/H11/H14` lub zbyt czuła delta `H07/H10/H13` | Zwiększ `H08/H11/H14` (np. `45 -> 60 min`) lub podnieś `H07/H10/H13` o `+1..2°C` (np. `10 -> 11–12°C`) |
| **Częste defrosty przy `0..+2°C` w trybie `Night`/`Eco`** | Wolniejszy wentylator (`P07`) słabiej owiewa parownik w wilgotnym powietrzu | Przy wilgotnej pogodzie `0..+2°C` przełącz `P07` na `Normal` albo skoryguj krzywą wentylatora `D09–D14` |
| **Temp. lamel skacze pod `+35..+45°C`**, a para leci długo po stopieniu lodu | Defrost grzeje na zewnątrz powietrze zamiast kończyć się po spłynięciu lodu | Lekko obniż `H04` (np. `15°C -> 12–13°C`) lub obniż moc defrostu `H01` (np. `70 -> 55–60 Hz`) |
| **Po defroście lód nie spływa do końca** (czas dochodzi do limitu `H05`) | Defrost kończy się za wcześnie lub ma za mało ciepła z instalacji | Podnieś `H04` (np. `15 -> 18°C`), sprawdź `H05` (`8–10 min`) i pilnuj dobrego przepływu wody CO podczas defrostu |
| **Grzałka tacy ociekowej stale aktywna** | Pobiera ok. `43 W` (`~1 kWh/dobę`), chroniąc odpływ skroplin przed zamarznięciem | Zjawisko normalne przy mrozach; czas pracy sprawdzisz w pomocnikach 24h |

### C. Jak czytać odfiltrowane sensory i zachowanie w trakcie defrostu

- **Zewnętrzna odfiltrowana (`ambient_temp_filtered`):** Zamraża temperaturę sprzed defrostu i trzyma blokadę po defroście przez `7 minut` **pracy wentylatora zewnętrznego** (lub maks. `45 minut` na postoju), aby nagrzane w obudowie powietrze po odszranianiu nie powodowało fałszywych skoków `+4°C`.
- **Obciążenie szronem (`coil_ambient_delta`):** Zawsze nieujemne — w trakcie aktywnego defrostu i gdy lamele są cieplejsze od powietrza przyjmuje `0.0 °C` (bez mylących skoków do `-40°C`). Wzrost w zakresie `4 -> 10 °C` w trakcie grzania pokazuje realne narastanie szronu na osobnym wykresie od `Temp. lamel`.
- **Ujemna `Delta T wody` i `Approach skraplacza` w defroście:** Pozostają surowe diagnostycznie — w trakcie defrostu obieg jest odwrócony (pompa pobiera chwilowo ciepło z wody), więc ujemna Delta T jest normalna, a Asystent nie podnosi już wtedy alarmu przepływu.
- **Opcjonalne wygładzanie w HA:** Pozostałe encje (`Obroty Hz`, `Water Delta T`, `Przegrzania`, `Szacowana moc`) nie są uśredniane w integracji, aby nie ukrywać prawdziwej dynamiki i nie opóźniać automatyzacji; drobne skoki `±1 Hz` / `±0.1°C` można wygładzić pomocnikiem HA `filter` lub `statistics` (np. średnia z `2–3 min`).
