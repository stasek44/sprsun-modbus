# 📖 Przewodnik po parametrach i ustawieniach pompy ciepła SPRSUN

## Spis treści
- [1. Parametry podstawowe (P)](#1-parametry-podstawowe-p)
- [2. Parametry ekonomiczne (E)](#2-parametry-ekonomiczne-e)
- [3. Parametry ogólne (G)](#3-parametry-ogólne-g)
- [4. Odczyty temperatury](#4-odczyty-temperatury)
- [5. Odczyty pracy systemu](#5-odczyty-pracy-systemu)
- [6. Statusy wejść i wyjść](#6-statusy-wejść-i-wyjść)
- [7. Alarmy i błędy](#7-alarmy-i-błędy)
- [8. Parametry zaawansowane](#8-parametry-zaawansowane)
- [9. Sterowanie](#9-sterowanie)

---

## 1. Parametry podstawowe (P)

### P01 - Heating Setpoint (0x00CC)
**Zakres:** 10-55°C | **Domyślnie:** ~45°C  
**Temperatura docelowa wody w trybie ogrzewania.**

- Ustawia żądaną temperaturę wody grzewczej (do grzejników/ogrzewania podłogowego)
- Wyższa wartość = cieplejsze pomieszczenia, ale wyższe zużycie energii
- Dla ogrzewania podłogowego: 30-40°C
- Dla grzejników: 45-55°C

### P02 - Cooling Setpoint (0x00CB)
**Zakres:** 12-30°C | **Domyślnie:** ~18°C  
**Temperatura docelowa wody w trybie chłodzenia.**

- Ustawia żądaną temperaturę wody chłodzącej (fan-coile, chłodzenie podłogowe)
- Niższa wartość = chłodniejsze pomieszczenia
- Typowo: 15-18°C dla chłodzenia aktywnego

### P03 - Temp Diff (Heating/Cooling) (0x00C6)
**Zakres:** 2-18°C | **Domyślnie:** 5°C  
**Histereza temperatury dla ogrzewania i chłodzenia.**

- Różnica temperatury, przy której pompa włącza/wyłącza się
- Przykład: Setpoint 45°C, diff 5°C → pompa wyłącza się przy 45°C, włącza przy 40°C
- Większa wartość = rzadsze cykle włącz/wyłącz (oszczędność energii, mniej komfortu)
- Mniejsza wartość = częstsze cykle (więcej komfortu, wyższe zużycie)

### P04 - Hot Water Setpoint (0x00CA)
**Zakres:** 10-55°C | **Domyślnie:** ~50°C  
**Temperatura docelowa ciepłej wody użytkowej (CWU).**

- Ustawia temperaturę wody w zasobniku CWU
- Typowo: 45-55°C
- **Uwaga:** Przy temp. <55°C zaleca się włączenie funkcji antylegionella

### P05 - Hot Water Temp Diff (0x00C8)
**Zakres:** 2-18°C | **Domyślnie:** 5°C  
**Histereza temperatury dla ciepłej wody użytkowej.**

- Różnica temp. przy której pompa podgrzewa CWU
- Przykład: Setpoint 50°C, diff 5°C → pompa włącza się przy 45°C

### P06 - Unit Mode (0x0036)
**Tryb pracy pompy ciepła.**

- **0 - DHW (Hot Water Only):** Tylko podgrzew CWU
- **1 - Heating Only:** Tylko ogrzewanie
- **2 - Cooling Only:** Tylko chłodzenie
- **3 - Heating + DHW:** Ogrzewanie + podgrzew CWU (typowy tryb zimowy)
- **4 - Cooling + DHW:** Chłodzenie + podgrzew CWU (typowy tryb letni)

**Wykorzystanie:**
- Zima: Tryb 3 (Heating + DHW)
- Lato: Tryb 4 (Cooling + DHW) lub 0 (tylko CWU)
- Okresowo: Tryb 0 dla szybkiego podgrzewu CWU

### P07 - Fan Mode (0x0190)
**Tryb pracy wentylatorów.**

- **0 - Normal:** Standardowa prędkość, optymalna wydajność
- **1 - Economic:** Wolniejsze obroty = cichsza praca, mniejsze zużycie energii, niższa wydajność
- **2 - Night:** Tryb nocny - minimalne obroty dla najcichszej pracy
- **3 - Test:** Tryb testowy - maksymalna wydajność

**Kiedy używać:**
- Normal: normalny dzień
- Economic: gdy priorytetem jest oszczędność
- Night: w nocy, aby nie przeszkadzać
- Test: diagnostyka, sprawdzanie wydajności

---

## 2. Parametry ekonomiczne (E)

**Idea:** Automatyczna zmiana temperatury docelowej w zależności od temp. zewnętrznej (krzywa grzewcza).

### E01-E04 - Economic Heat Ambient (0x0169-0x016C)
**Zakres:** -30 do 50°C | **Temperatury zewnętrzne - punkty krzywej ogrzewania**

Definiuje 4 punkty temperatury otoczenia dla trybu Economic Heating:
- **E01:** Najniższa temp. zewnętrzna (np. -20°C)
- **E02:** Niska temp. (np. -10°C)
- **E03:** Średnia temp. (np. 0°C)
- **E04:** Wysoka temp. (np. 10°C)

### E13-E16 - Economic Heat Temp (0x0175-0x0178)
**Zakres:** 10-55°C | **Temperatury docelowe wody - punkty krzywej ogrzewania**

Odpowiadające temperatury docelowe wody:
- **E13:** Temp. wody gdy na zewnątrz E01 (np. 55°C przy -20°C)
- **E14:** Temp. wody gdy na zewnątrz E02 (np. 50°C przy -10°C)
- **E15:** Temp. wody gdy na zewnątrz E03 (np. 45°C przy 0°C)
- **E16:** Temp. wody gdy na zewnątrz E04 (np. 35°C przy 10°C)

**Przykład działania:**
```
Temp. zewnętrzna -15°C → Pompa interpoluje między E01(-20°C)→E13(55°C) a E02(-10°C)→E14(50°C)
Wynik: Temp. docelowa wody ~52-53°C
```

### E05-E08 - Economic Water Ambient (0x016D-0x0170)
**Zakres:** -30 do 50°C | **Punkty krzywej dla CWU**

Jak E01-E04, ale dla ciepłej wody użytkowej.

### E17-E20 - Economic Water Temp (0x0179-0x017C)
**Zakres:** 10-55°C | **Temperatury docelowe CWU**

Odpowiadające E05-E08 temperatury docelowe CWU.

### E09-E12 - Economic Cool Ambient (0x0171-0x0174)
**Zakres:** -30 do 50°C | **Punkty krzywej dla chłodzenia**

Jak E01-E04, ale dla trybu chłodzenia.

### E21-E24 - Economic Cool Temp (0x017D-0x0180)
**Zakres:** 12-30°C | **Temperatury docelowe chłodzenia**

Odpowiadające E09-E12 temperatury docelowe wody chłodzącej.

**Kiedy używać trybu Economic:**
- Automatyczna optymalizacja w zależności od pogody
- Oszczędność energii - nie przegrzewa/przechładza
- Idealny na cały sezon grzewczy/chłodzący

---

## 3. Parametry ogólne (G)

### G02 - Pump Work Mode (0x019E)
**Tryb pracy pompy obiegowej.**

- **0 - Interval:** Pompa pracuje cyklicznie (np. 3 min co 30 min) - zapobiega zatrzymaniu i zamarzaniu podczas dłuższych przerw w pracy
- **1 - Normal:** Pompa pracuje ciągle gdy pompa ciepła w trybie ogrzewania/chłodzenia (Always On)
- **2 - Demand:** Pompa pracuje tylko gdy jest faktyczne zapotrzebowanie - najbardziej ekonomiczny

**Wybór trybu:**
- **Interval**: Gdy pompa jest wyłączona przez długi czas (np. tylko CWU latem) - chroni przed zamarzaniem. W tym trybie pompa włącza się okresowo (interwał ustawiany fabrycznie, typowo 30 minut) na krótki czas (typowo 3 minuty) aby zapewnić cyrkulację i zapobiec zamarzaniu.
- **Normal**: Standardowy tryb - ciągła cyrkulacja zapewnia równomierne ogrzewanie/chłodzenie
- **Demand**: Oszczędność energii - pompa włącza się tylko gdy potrzeba. Uwaga: może skutkować częstszymi cyklami włącz/wyłącz pompy ciepła

**Informacje o pompie DC/inverter:**
Jeśli masz pompę DC (ze zmienną prędkością), to:
- W trybie Normal lub Demand pompa automatycznie reguluje prędkość według G04 (Delta Temp Set)
- Parametr G04 określa docelową różnicę temperatur między zasilaniem a powrotem
- Im wyższa różnica temperatur ustawiona, tym wolniej pracuje pompa = oszczędność energii

**Zalecane:** Normal dla instalacji grzewczej, Demand gdy priorytetem jest oszczędność energii

### G03 - Start Interval (0x0185)
**Zakres:** 1-120 minut | **Minimalny odstęp między startami sprężarki**

- Chroni sprężarkę przed zbyt częstym włączaniem
- Typowo: 5-10 minut
- Zbyt krótki = zużycie sprężarki
- Zbyt długi = mniejszy komfort

### G04 - DC Pump Temp Differential (0x018D)
**Zakres:** 5-30°C | **Różnica temp. dla sterowania pompą DC**

- Przy pompie obiegowej ze sterowaniem prędkości (DC/inverter)
- Określa różnicę temp. między zasilaniem a powrotem do regulacji prędkości pompy
- **Zasada działania**: Pompa DC automatycznie dostosowuje prędkość aby utrzymać zadaną różnicę temperatur między wyjściem a powrotem
- Wyższa wartość (np. 10-15°C) = wolniejsza pompa = większe ∆T = oszczędność energii ale mniejszy komfort
- Niższa wartość (np. 5-8°C) = szybsza pompa = mniejsze ∆T = lepsze mieszanie i równomierność temperatur

**Uwaga**: Ten parametr działa tylko gdy masz pompę DC/inverter. Przy standardowej pompie stałoprędkościowej parametr jest ignorowany.

### G05 - Heating Heater External Temp (0x0184)
**Zakres:** -30 do 30°C | **Temperatura aktywacji dogrzewu dla ogrzewania**

- Poniżej tej temp. zewnętrznej włącza się grzałka elektryczna wspomagająca ogrzewanie (OUT4)
- Typowo: -10°C do -5°C (zależy od mocy pompy)
- Niższa wartość = rzadsze użycie dogrzewu (oszczędność prądu)

**Ważne informacje o dogrzewie:**
- Grzałka elektryczna pobiera dużo prądu (typowo 3-9 kW)
- Zaleca się używanie tylko jako wspomaganie w ekstremalnie niskich temperaturach
- Fabryczne okablowanie łączy grzałkę ogrzewania na wyjściu OUT4
- Grzałka powinna być typu przepływowego, zamontowana w rurze zasilania instalacji
- Opóźnienie włączenia grzałki ustawiane jest w G06

### G06 - Heating Heater Delay (0x0182)
**Zakres:** 1-60 minut | **Opóźnienie włączenia dogrzewu ogrzewania**

- Czas oczekiwania przed włączeniem grzałki elektrycznej
- Daje pompie ciepła szansę na osiągnięcie temp. bez dogrzewu
- Typowo: 10-30 minut

### G07 - Hot Water Heater External Temp (0x0183)
**Zakres:** -30 do 30°C | **Temperatura aktywacji dogrzewu dla CWU**

- Jak G05, ale dla podgrzewu CWU (OUT12)
- Poniżej tej temp. zewnętrznej używa grzałki do szybszego podgrzewu CWU
- Fabryczne okablowanie łączy grzałkę CWU na wyjściu OUT12
- Grzałka powinna być zamontowana w zasobniku CWU lub w rurze przepływowej CWU
- Opóźnienie włączenia grzałki ustawiane jest w G08

**Uwaga**: Jeśli używasz własnych grzałek (nie z zestawu producenta), upewnij się że są to grzałki przepływowe zainstalowane we właściwej ścieżce przepływu wody zgodnie z dokumentacją instalacyjną.

### G08 - Hot Water Heater Delay (0x0181)
**Zakres:** 1-60 minut | **Opóźnienie włączenia dogrzewu CWU**

- Jak G06, ale dla CWU

### G09 - Mode Control Enable (0x0191)
**Automatyczne przełączanie trybów w zależności od temp. zewnętrznej.**

- **0 - NO linkage (Manual):** Tryb ustawiany ręcznie przez P06 (Unit Mode) - bez automatyki
- **1 - YES amb (Automatic):** Automatyczne przełączanie heating/cooling w zależności od temperatury zewnętrznej (G10/G11)

**Jak działa tryb automatyczny:**
1. Ustaw G10 (punkt przełączania, np. 20°C)
2. Ustaw G11 (histereza, np. 3°C)
3. Gdy temp. zewnętrzna > G10 + G11 (np. >23°C) → automatycznie przełącza na cooling lub cooling+DHW
4. Gdy temp. zewnętrzna < G10 - G11 (np. <17°C) → automatycznie przełącza na heating lub heating+DHW  
5. Między 17-23°C → utrzymuje aktualny tryb (bez przełączania)

**Przykład użycia:**
Latem gdy temperatura rośnie powyżej 23°C, pompa automatycznie przełącza się na chłodzenie. Jesienią gdy temperatura spada poniżej 17°C, automatycznie wraca do ogrzewania.

**Uwaga**: CWU pozostaje aktywne w obu trybach (jeśli wybrano tryb z +DHW w P06).

### G10 - Ambient Switch Setpoint (0x0192)
**Zakres:** -20 do 30°C | **Punkt przełączenia trybu (temp. zewnętrzna)**

- Próg temperatury zewnętrznej dla automatycznego przełączania heating ↔ cooling
- Typowo: 18-22°C

### G11 - Ambient Switch Diff (0x0193)
**Zakres:** 1-10°C | **Histereza przełączania trybu**

- Zapobiega częstemu przełączaniu
- Przykład: G10=20°C, G11=3°C
  - Przełącza na cooling gdy temp > 23°C
  - Przełącza na heating gdy temp < 17°C

---

## 4. Odczyty temperatury

### Czujniki wody

**Inlet Temperature (0x000E)** - Temperatura wody na wejściu (powrót z instalacji)  
- Pokazuje jak bardzo obieg oddał/odebrał energię
- Niższa w trybie heating, wyższa w cooling

**Outlet Temperature (0x0012)** - Temperatura wody na wyjściu (zasilanie instalacji)  
- Temperatura którą pompa wysyła do instalacji
- Wyższa w trybie heating, niższa w cooling

**Hot Water Temperature (0x000F)** - Temperatura wody w zasobniku CWU  
- Monitorowanie stanu podgrzewu CWU

### Czujniki czynnika (R410A/R32)

**Ambient Temperature (0x0011)** - Temperatura otoczenia (powietrza zewnętrznego)  
⚠️ **MOŻE BYĆ UJEMNA** (signed)  
- Kluczowy parametr dla krzywych grzewczych i automatyki
- Wpływa na wydajność pompy

**Suction Gas Temperature (0x0015)** - Temperatura gazu ssania (przed sprężarką)  
⚠️ **MOŻE BYĆ UJEMNA** (signed)  
- Temperatura czynnika po parowaniu
- Wskaźnik wydajności parownika
- Typowo: -5 do +10°C (heating mode)

**Discharge/Exhaust Temperature (0x001B)** - Temperatura gazu tłoczenia (po sprężarce)  
- Temperatura czynnika po sprężaniu
- Typowo: 60-85°C
- **Alarm jeśli > 95-100°C** (przegrzanie)

**Driving Temperature (0x0022)** - Temperatura silnika/falownika sprężarki  
⚠️ **MOŻE BYĆ UJEMNA** (signed, ale rzadko)  
- Monitorowanie temperatury układu napędowego
- Alarm jeśli za wysoka

**Coil Temperature (0x0016)** - Temperatura wymiennika wężownicy  
⚠️ **MOŻE BYĆ UJEMNA** (signed)  
- Temperatura cewki wymiennika
- W trybie heating: temperatura skraplacza
- W trybie cooling: temperatura parownika

**Evaporator Temperature (0x0028)** - Temperatura parownika  
⚠️ **MOŻE BYĆ UJEMNA** (signed, często!)  
- Temperatura parowania czynnika
- Heating mode: ujemna (parownik na zewnątrz, odbiera ciepło z powietrza)
- Cooling mode: dodatnia
- Typowo: -10 do +5°C (heating)

**Condenser Temperature (0x0029)** - Temperatura skraplacza  
- Temperatura skraplania czynnika
- Typowo: 35-50°C

### Ciśnienia

**Suction/Discharge Pressure (0x002F/0x0030)** - Ciśnienie ssania/tłoczenia  
⚠️ **W KODZIE REJESTRY SĄ ZAMIENIONE!**
- 0x002F = faktycznie **discharge** (~15-30 bar)
- 0x0030 = faktycznie **suction** (~4-7 bar)
- Jednostka: bar (0.1 PSI → bar)
- Monitorowanie pracy obiegu czynnika
- Za wysokie/niskie = alarm i wyłączenie

---

## 5. Odczyty pracy systemu

### Wydajność

**COP (0x0001)** - Coefficient of Performance  
- Współczynnik wydajności = Energia oddana / Energia pobrana
- Przykład: COP=4 → za 1 kW energii elektrycznej dostajesz 4 kW ciepła
- Typowo: 3-5 (zależy od temp. zewnętrznej)

**Heating/Cooling Capacity (0x0019)** - Aktualna moc grzewcza/chłodząca [W]  
- Faktyczna wydajność pompy w danym momencie
- Zależy od temperatury zewnętrznej i obciążenia

**EEV1/EEV2 Step (0x001C/0x001D)** - Pozycja zaworu rozprężnego elektronicznego  
- Reguluje przepływ czynnika
- Wartość 0-500 kroków
- Automatycznie sterowana przez pompę

### Elektryka

**AC Voltage (0x0017)** - Napięcie zasilania [V]  
**AC Current (0x001A)** - Prąd pobierany [A]  
- Monitoring zasilania
- AC Current × AC Voltage ≈ moc pobierana

**DC Bus Voltage (0x0021)** - Napięcie magistrali DC falownika [V]  
- Wewnętrzne napięcie układu sterowania falownikiem
- Typowo: 300-380V

**Compressor Current (0x0023)** - Prąd sprężarki [A]  
- Faktyczny prąd pobierany przez sprężarkę

### Sprężarka i wentylatory

**Compressor Frequency (0x001E)** - Częstotliwość pracy sprężarki [Hz]  
- Aktualne obroty sprężarki
- Zakres: 30-120 Hz (zależy od modelu)
- Wyższa = więcej mocy

**Target Frequency (0x0024)** - Docelowa częstotliwość sprężarki [Hz]  
- Żądane obroty (pompa dąży do tej wartości)

**DC Fan 1/2 Speed (0x0026/0x0027)** - Prędkość wentylatorów [RPM]  
- Aktualne obroty wentylatorów wymiennika zewnętrznego

**DC Fan Target (0x0031)** - Docelowa prędkość wentylatora  
- Żądane obroty wentylatorów

**DC Pump Speed (0x002E)** - Prędkość pompy DC [%]  
- Jeśli masz pompę z regulacją prędkości

### Przepływ

**Pump Flow (0x0018)** - Przepływ wody [m³/h]  
- Ilość wody przepływającej przez pompę ciepła
- Typowo: 1-3 m³/h (zależy od instalacji)

### Statystyki

**Compressor Runtime (0x0000)** - Całkowity czas pracy sprężarki [h]  
- Licznik motogodzin dla serwisu
- Pomaga planować przeglądy

**Software/Controller/Display Version (0x0013/0x0014/0x002C/0x002D)**  
- Wersje oprogramowania komponentów
- Przydatne dla serwisu i aktualizacji

---

## 6. Statusy wejść i wyjść

### Switching Input Symbol (0x0002) - Statusy wejść cyfrowych

**A/C Linkage Switch (bit 0)** - Sygnał z klimatyzacji  
**Linkage Switch (bit 1)** - Główny sygnał sprzężenia  
**Heating Linkage (bit 2)** - Żądanie ogrzewania z termostatu  
**Cooling Linkage (bit 3)** - Żądanie chłodzenia z termostatu  
**Flow Switch (bit 4)** - Czujnik przepływu wody (zabezpieczenie)  
**High Pressure Switch (bit 5)** - Czujnik wysokiego ciśnienia (zabezpieczenie)  
**Phase Sequence (bit 6)** - Detekcja kolejności faz (3-fazowe)  

**Interpretacja:** 
- 0 = nieaktywny/rozwarty
- 1 = aktywny/zwarty

**Linkage** = fizyczne wejścia dla sprzężenia z innymi urządzeniami (termostaty, klimatyzacja)

### Working Status Mark (0x0003) - Status pracy

**Hot Water Demand (bit 0)** - Zapotrzebowanie na CWU  
**Heating Demand (bit 1)** - Zapotrzebowanie na ogrzewanie  
**With/Without Heating (bit 2)** - Funkcja ogrzewania dostępna  
**With/Without Cooling (bit 3)** - Funkcja chłodzenia dostępna  
**Antilegionella Active (bit 4)** - Dezynfekcja antylegionella trwa  
**Cooling Demand (bit 5)** - Zapotrzebowanie na chłodzenie  
**Alarm Stop (bit 6)** - Zatrzymanie z powodu alarmu  
**Defrost Active (bit 7)** - Trwa odszranianie wymiennika  

### Output Symbol 1 (0x0004) - Statusy wyjść głównych

**Compressor (bit 0)** - Sprężarka pracuje  
**Fan (bit 5)** - Wentylator wymiennika pracuje  
**4-Way Valve (bit 6)** - Zawór 4-drogowy (heating=0, cooling=1)  
**Fan High Speed (bit 7)** - Wentylator na wysokich obrotach (0=low, 1=high)  

### Output Symbol 2 (0x0005) - Statusy wyjść dodatkowych

**Chassis Heater (bit 0)** - Grzałka skrzyni sprężarki (chroni przy niskich temp.)  
**Heating Heater (bit 5)** - Grzałka dogrzewu dla ogrzewania  
**3-Way Valve (bit 6)** - Zawór 3-drogowy (CWU/heating)  
**Hot Water Heater (bit 7)** - Grzałka dogrzewu dla CWU  

### Output Symbol 3 (0x0006) - Statusy wyjść pompy

**A/C Pump (bit 0)** - Pompa klimatyzacji  
**Crank Heater (bit 1)** - Grzałka skrzyni korbowej (ochrona zimowa)  
**Assistant Solenoid Valve (bit 5)** - Pomocniczy zawór elektromagnetyczny  
**Circulation Pump (bit 6)** - Pompa obiegowa instalacji  

---

## 7. Alarmy i błędy

### Failure Symbol 1 (0x0007) - Błędy czujników temperatury

**Hot Water Temp Sensor (bit 0)** - Uszkodzony czujnik temp. CWU  
**Ambient Temp Sensor (bit 1)** - Uszkodzony czujnik temp. otoczenia  
**Coil Temp Sensor (bit 2)** - Uszkodzony czujnik temp. cewki  
**Outlet Temp Sensor (bit 4)** - Uszkodzony czujnik temp. wylotu  
**High Pressure Sensor (bit 5)** - Uszkodzony czujnik wysokiego ciśnienia  
**Phase Sequence Error (bit 7)** - Błędna kolejność faz (tylko 3-fazowe)  

**Akcja:** Sprawdź okablowanie czujnika, wymień jeśli uszkodzony

### Failure Symbol 2 (0x0008) - Błędy przepływu i zabezpieczeń

**Water Flow Error (bit 0)** - Brak przepływu wody  
- Sprawdź: pompę obiegową, filtry, powietrze w instalacji, zawory

**High Temp Protection (bit 2)** - Za wysoka temp. wody na wylocie (heating)  
- Sprawdź: przepływ, obciążenie instalacji

### Failure Symbol 3 (0x0009) - Błędy sensora gazu

**Outlet Gas Temp Error (bit 6)** - Uszkodzony czujnik temp. gazu wylotowego  

### Failure Symbol 4 (0x000A) - Błędy temperatury

**Water Inlet Temp Error (bit 0)** - Uszkodzony czujnik temp. wejścia wody  
**Exhaust Temp Too High (bit 1)** - Przegrzanie gazu tłoczenia (>100°C)  
- **POWAŻNY BŁĄD** - pompa wyłącza się dla ochrony sprężarki

**Low Temp Protection (bit 5)** - Za niska temp. wody na wylocie (cooling)  
- Ochrona przed zamarzaniem

**Inlet Gas Temp Error (bit 6)** - Uszkodzony czujnik temp. gazu ssania  

### Failure Symbol 5 (0x000B) - Błędy ciśnienia (NAJWAŻNIEJSZE!)

**Low Pressure Protection (bit 0)** - Za niskie ciśnienie ssania  
- Przyczyny: za mało czynnika, zatkany filtr, problem z parownikiem
- **Akcja:** Wezwij serwis, sprawdź szczelność, doładuj czynnik

**High Pressure Protection (bit 1)** - Za wysokie ciśnienie tłoczenia  
- Przyczyny: za dużo czynnika, zatkany skraplacz, wentylatory nie działają
- **Akcja:** Wezwij serwis, sprawdź wentylatory i wymiennik

**Coil Temp Too High (bit 2)** - Przegrzanie cewki wymiennika  

**High/Low Pressure Sensors (bit 6/7)** - Uszkodzone czujniki ciśnienia  

### Failure Symbol 6 (0x000C) - Błędy antyfreeze

**Primary/Secondary Antifreeze (bit 4/5)** - Ochrona przed zamarzaniem  
- Pompa wykryła ryzyko zamarzania wymiennika lub instalacji
- Sprawdź przepływ, temperaturę zewnętrzną

### Failure Symbol 7 (0x000D) - Błędy systemowe

**Ambient Temp Too Low (bit 1)** - Temperatura otoczenia poniżej granicy pracy  
- Pompy ciepła mają dolną granicę temp. pracy (np. -20°C)

**Inverter Module Fault (bit 4)** - Awaria falownika sprężarki  
- **POWAŻNY BŁĄD** - wezwij serwis

**DC Fan 1/2 Failure (bit 5/6)** - Awaria wentylatora 1 lub 2  
- Sprawdź wentylatory, okablowanie, sterowanie

---

## 8. Parametry zaawansowane

### Antilegionella (Dezynfekcja CWU)

**Temperatura (0x019A):** 30-70°C (zalecane 60°C)  
**Dzień tygodnia (0x019B):** 0=Niedziela, 1=Poniedziałek... 6=Sobota  
**Godzina rozpoczęcia (0x019C):** 0-23  
**Godzina zakończenia (0x019D):** 0-23  

**Cel:** Zabicie bakterii Legionella w zasobniku CWU przez okresowe podgrzanie do 60°C.  
**Przykład:** Co niedzielę (0) od 3:00 (0x019C=3) do 5:00 (0x019D=5) podgrzej CWU do 60°C (0x019A=60).

**Kiedy włączać:**
- CWU normalnie poniżej 55°C
- Zasobnik > 100L
- Długie okresy bez rozbioru CWU

### Frequency Conversion Failure (0x001F/0x0020/0x002A/0x002B)

Kody błędów falownika sprężarki. Wartości specyficzne dla modelu falownika.  
Jeśli widzisz błąd = wezwij serwis z kodem błędu.

### Smart Grid Status (0x0025)

Status komunikacji z inteligentną siecią energetyczną (Smart Grid).  
Pozwala na sterowanie pompą przez operatora sieci (zmniejszenie poboru w szczycie).

---

## 9. Sterowanie

### Power Switch (0x0032 bit 0)

**ON/OFF główne pompy ciepła.**

- 0 = OFF (pompa wyłączona, standby)
- 1 = ON (pompa pracuje według ustawień)

**Uwaga:** To nie jest wyłącznik awaryjny - używa normalnej procedury wyłączania.

### Failure Reset (0x0033 bit 7)

**Przycisk resetowania błędów.**

- Zapisz 1 aby zresetować alarmy (po usunięciu przyczyny)
- Automatycznie wraca do 0

**Kiedy używać:**
- Po naprawieniu przyczyny błędu
- Po sprawdzeniu że instalacja jest OK
- **NIE resetuj bez zrozumienia przyczyny!**

### Control Mark 2 (0x0034)

**Antilegionella Enable (bit 0):** Włącz/wyłącz funkcję antylegionella  
- 0 = Wyłączona (domyślnie)
- 1 = Włączona
- Jeśli włączona, pompa będzie okresowo (zgodnie z parametrami 0x019A-0x019D) podgrzewać CWU do wysokiej temperatury (60°C) aby zabić bakterie Legionella

**Two/Three Function (bit 1, G01):** Konfiguracja funkcjonalności pompy  
- **0 = Two (Dwufunkcyjna):** Pompa obsługuje **2 funkcje**: Ogrzewanie + Chłodzenie (bez CWU)
  - Nie ma trzeciego wymiennika dla CWU
  - Pompa może tylko grzać lub chłodzić instalację
  - Tryby dostępne w P06: Heating Only (1), Cooling Only (2)
  
- **1 = Three (Trójfunkcyjna):** Pompa obsługuje **3 funkcje**: Ogrzewanie + Chłodzenie + CWU (standard)
  - Ma trzeci wymiennik/zawór 3-drogowy dla podgrzewu CWU
  - Pompa może grzać/chłodzić instalację ORAZ podgrzewać CWU
  - Tryby dostępne w P06: DHW Only (0), Heating Only (1), Cooling Only (2), Heating+DHW (3), Cooling+DHW (4)

**Kiedy zmienić:**
- **Two**: Jeśli nie masz zasobnika CWU lub używasz innego źródła do podgrzewu CWU (np. kocioł elektryczny)
- **Three**: Standardowa konfiguracja - pompa obsługuje wszystko (heating + cooling + DHW)

**Uwaga**: Ten parametr powinien odpowiadać fizycznej konfiguracji instalacji. Nieprawidłowe ustawienie może powodować błędy pracy pompy.

---

## 📝 Praktyczne wskazówki

### Optymalizacja energetyczna

1. **Używaj krzywych grzewczych (Economic mode)** - automatyczna adaptacja do pogody
2. **Ustaw odpowiednią histerezę (P03/P05)** - 5-8°C to dobry kompromis
3. **Fan Mode = Economic** gdy nie potrzebujesz max wydajności
4. **Temperatura CWU = 50°C** + antylegionella (oszczędność vs bezpieczeństwo)
5. **G05/G07 jak najniżej** - ogranicza użycie dogrzewu elektrycznego

### Rozwiązywanie problemów

**Pompa często się włącza/wyłącza:**
- Zwiększ histerezę (P03/P05)
- Sprawdź G03 (Start Interval)

**Za zimno w domu:**
- Zwiększ P01 (Heating Setpoint)
- Sprawdź krzywą grzewczą (E01-E16)
- Sprawdź czy nie ma błędów ciśnienia

**Za mało CWU:**
- Zwiększ P04 (Hot Water Setpoint)
- Sprawdź czy P06 = DHW lub Heating+DHW lub Cooling+DHW
- Zmniejsz P05 (uruchomi się wcześniej)

**Alarmy ciśnienia:**
- **Low pressure:** Wyciek czynnika - wezwij serwis
- **High pressure:** Zatkany wymiennik, wentylatory - sprawdź wymiennik, wyczyść

**Hałas nocą:**
- P07 = Night Mode
- Sprawdź montaż (wibracje)
- Zwiększ G03 (rzadsze starty)

### Monitorowanie

**Regularnie sprawdzaj:**
- COP - powinien być 3-5 (jeśli niższy = problem)
- Ciśnienia - ssanie 4-7 bar, tłoczenie 15-30 bar
- Temp. tłoczenia - nie powinna przekraczać 85°C
- Błędy - reaguj na alarmy natychmiast

**Wskaźniki problemów:**
- COP < 2.5 = problem z wydajnością
- Temp. tłoczenia > 90°C = przegrzanie
- Częste cykle on/off = źle dobrana histereza
- Alarmy ciśnienia = natychmiast serwis!

---

## 🔗 Dodatkowe informacje

**Ważne:**
- Zmiany parametrów działają tylko dla urządzenia #1 (device_address=1)
- Przed zmianą zaawansowanych parametrów skonsultuj z serwisem
- Zapisuj oryginalne wartości przed eksperymentowaniem
- Niektóre parametry mogą wymagać restartu pompy

**W razie wątpliwości:**
- Skonsultuj z instalatorem
- Sprawdź instrukcję obsługi producenta
- Wezwij autoryzowany serwis

