# Deutsche Archiv RSS-Feeds

Dieses Repository generiert automatisch RSS-Feeds für deutsche Archive, die von Haus aus keinen eigenen Feed anbieten.

## Verfügbare Feeds

| Archiv | Feed |
| --- | --- |
| [Bundesarchiv Aktuelles](https://www.bundesarchiv.de/aktuelles/) | [feed_bundesarchiv.xml](./feeds/feed_bundesarchiv.xml) |

## Wie es funktioniert

Ein GitHub-Workflow prüft am Tag zweimal auf neue Inhalte auf den Webseiten der Archive. Wenn neue Beiträge gefunden werden, wird die entsprechende XML-Datei im Ordner `feeds/` aktualisiert.

## Neue Feeds ohne viel Python-Know-how anlegen

Für neue Quellen ist jetzt auch ein einfacher, konfigurationsbasierter Weg möglich. Ein neuer Feed kann über eine Eintrag in `feeds.yaml` angelegt werden, ohne dass sofort eigener Python-Code geschrieben werden muss.

1. Öffne `feeds.yaml` und ergänze einen Eintrag wie diesen:

   ```yaml
   feeds:
     mein_feed:
       script: generic_feed.py
       type: requests
       blog_url: https://example.org/aktuelles/
       title: Mein Feed
       description: Beschreibung des Feeds
       selectors:
         article_selector: article.post
         title_selector: h2 a
         link_selector: h2 a
         description_selector: p
         date_selector: time
         date_attr: datetime
         date_format: "%Y-%m-%d"
         base_url: https://example.org
   ```

2. Passe die CSS-Selektoren an die Zielseite an.
3. Erzeuge den Feed mit:

   ```bash
   uv run python feed_generators/run_all_feeds.py --feed mein_feed
   ```

Für einen frischen Start kann auch das Hilfsskript verwendet werden:

```bash
uv run python feed_generators/add_feed.py mein_feed
```

## Installation & Entwicklung

Dieses Projekt nutzt `uv` für das Python-Paketmanagement.

1.  Abhängigkeiten installieren:
    ```bash
    uv sync
    ```

2.  Feed manuell generieren:
    ```bash
    uv run python feed_generators/bundesarchiv_blog.py
    ```

## Rechtliches

Die Scripte basieren auf dem Projekt [rss-feeds](https://github.com/Olshansk/rss-feeds) von Olshansk.
