### Installation

Project MRT benötigt entweder die Installtion von Python sowie Tesseract OCR oder Docker.
Es wird empfohlen, Docker zu nutzen, da dies einfacher ist. Aus diesem Grund wird folgend lediglich die Nutzung über Docker erklärt.

1. Das Repository herunterladen.
2. Eingabeaufforderung (oder alternativ PowerShell) öffnen.
3. in den Ordner des heruntergeladenen Repositories navigieren (per 'cd'-Command)
4. Eingabe des folgenden Codes:
```sh
docker-compose build
docker-compose up
```
5. Nachdem der Container gebaut und ausgeführt wird, kann über einen Browser über "localhost:8000" die Anwendung geöffnet werden.

Zu beachten:
Docker nutzt für diesen Container den Port 8000, weshalb sichergestellt werden sollte, dass dieser Port nicht belegt ist.

Bei Fragen oder Problemen melden Sie sich gerne bei dem Projektteam.
