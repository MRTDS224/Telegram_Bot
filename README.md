# TelegramBot

Ce dépôt contient plusieurs versions d'un bot Telegram en Python, conçu pour la transcription vocale et la traduction.

## Contenu principal

- `Bot trans-trad.py` : version du bot pour transcription et traduction.
- `Bot tt modifié.py` : version modifiée du bot.
- `Bot MM.py` : autre version du bot avec des fonctionnalités supplémentaires.
- `L'autre Bot.py` : autre script de bot Telegram.
- `text_to_speech.py` : script de synthèse vocale.
- `requirements.txt` : dépendances Python nécessaires.

## Installation

1. Créez un environnement virtuel Python.
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Définissez la variable d'environnement `TELEGRAM_TOKEN` avec le jeton de votre bot.

## Exécution

Exécutez l’un des scripts de bot, par exemple :

```bash
python "Bot trans-trad.py"
```

## Notes

- Les jetons et autres informations sensibles ne doivent jamais être hardcodés dans le code.
- Utilisez un fichier `.env` ou les variables d’environnement pour stocker `TELEGRAM_TOKEN`.
