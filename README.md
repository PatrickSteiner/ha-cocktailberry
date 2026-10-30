# CocktailBerry für Home Assistant

Custom Integration (HACS) für eine Cocktailmaschine mit [CocktailBerry](https://github.com/AndreWohnsland/CocktailBerry) **v2** (Web-Version). Sie spricht direkt mit der REST-API auf dem Raspberry Pi – kein MQTT, kein Addon auf dem Pi nötig.

## Voraussetzungen

- CocktailBerry v2 läuft (`setup-web`), die API ist unter `http://<pi>:8000/api` erreichbar
- Home Assistant 2025.6 oder neuer, HACS installiert

Test vom Rechner aus: `http://<pi>:8000/api/info` muss JSON mit `"project_name": "CocktailBerry"` liefern.

## Installation über HACS

1. Dieses Repository auf GitHub anlegen (Inhalt dieses Ordners ins Root).
2. HACS → ⋮ → *Benutzerdefinierte Repositories* → URL eintragen, Typ **Integration**.
3. „CocktailBerry“ installieren, Home Assistant neu starten.
4. *Einstellungen → Geräte & Dienste → Integration hinzufügen → CocktailBerry*: IP des Pi, Port `8000`, Maker-Passwort nur falls in CocktailBerry gesetzt.

Manuell geht es auch: `custom_components/cocktailberry` nach `/config/custom_components/` kopieren und neu starten.

## Was du bekommst

| Entität | Inhalt |
|---|---|
| `sensor.cocktailberry_status` | Bereit / Mixt / Fertig / Abgebrochen / Zu wenig Zutaten … ; Attribut `hand_adds` (Handzugaben) |
| `sensor.cocktailberry_fortschritt` | Fortschritt in % |
| `binary_sensor.cocktailberry_mixt` | an, solange gemixt wird |
| `sensor.cocktailberry_flasche_1` … | Füllstand in %; Zutat, ml und Flaschenvolumen als Attribute |
| `sensor.cocktailberry_verfugbare_cocktails` | Anzahl mixbarer Cocktails, Liste als Attribut |
| `sensor.cocktailberry_letzter_cocktail` | Name des zuletzt aus HA gestarteten Cocktails |
| `select.cocktailberry_cocktail`, `number.…_menge`, `number.…_starke`, `switch.…_alkoholfrei` | Auswahl für den nächsten Cocktail |
| `button.cocktailberry_cocktail_mixen` | startet die Auswahl (nur wenn erlaubt, s. u.) |
| `button.cocktailberry_zubereitung_stoppen` | bricht ab |

Status wird alle 3 s abgefragt, Flaschen und Rezepte jede Minute und direkt nach jedem Cocktail.

## Cocktails aus HA starten (standardmäßig aus)

Aus Home Assistant sieht niemand, ob ein Glas unter dem Auslauf steht. Deshalb ist das Starten aus HA erst möglich, wenn du es in den **Optionen der Integration** einschaltest („Cocktails aus Home Assistant starten erlauben“). Erst dann erscheint der Mix-Button und der Dienst funktioniert.
Mit Wägezelle + Glass-Detection-Addon in CocktailBerry lehnt die Maschine selbst ab, wenn kein Glas steht (Status „Kein Glas erkannt“).

## Dienste

```yaml
action: cocktailberry.prepare_cocktail
data:
  cocktail: Sidecar        # Name oder Rezept-ID
  volume: 200              # ml
  alcohol_factor: 100      # % des Rezepts
  virgin: false
```

`cocktailberry.stop_preparation` und `cocktailberry.refresh` ohne Parameter.

## Ereignisse für Automationen

- `cocktailberry_preparation_started` – `cocktail` (nur bei Start aus HA bekannt), `status`
- `cocktailberry_preparation_ended` – `cocktail`, `status` (`FINISHED`, `CANCELED`, …), `message`, `hand_adds`

Beispiel: Benachrichtigung, wenn eine Flasche unter 15 % fällt:

```yaml
triggers:
  - trigger: numeric_state
    entity_id:
      - sensor.cocktailberry_flasche_1
      - sensor.cocktailberry_flasche_2
    below: 15
actions:
  - action: notify.notify
    data:
      message: >
        {{ state_attr(trigger.entity_id, 'ingredient') }} ist fast leer
        ({{ trigger.to_state.state }} %).
```

## Grenzen

- Funktioniert nur mit CocktailBerry **v2** (v1 hat keinen Webserver).
- Die API meldet nicht, *welcher* Cocktail gerade läuft; bei Start am Touchscreen ist der Name in HA daher leer.
- Zu viele falsche Passwörter sperren den Client kurz (HTTP 429); HA fragt dann das Passwort neu ab.
