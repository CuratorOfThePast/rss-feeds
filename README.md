# Deutsche Archiv RSS-Feeds

Dieses Repository generiert automatisch RSS-Feeds für deutsche Archive, die von Haus aus keinen eigenen Feed anbieten.

## Verfügbare Feeds

| Archiv | Feed |
| --- | --- |
| [Bundesarchiv Aktuelles](https://www.bundesarchiv.de/aktuelles/) | [feed_bundesarchiv.xml](./feeds/feed_bundesarchiv.xml) |

## Wie es funktioniert

Ein GitHub-Workflow prüft am Tag zweimal auf neue Inhalte auf den Webseiten der Archive. Wenn neue Beiträge gefunden werden, wird die entsprechende XML-Datei im Ordner `feeds/` aktualisiert.

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
