# sarvam-AI


## What the code currently does

This is a Flask web application serving `index.html` and exposing `/api/speech-to-text` and `/api/chat`. It sends audio to Sarvam AI Saaras v3 for language detection and speech recognition, then uses Sarvam chat completion to answer salon questions in the detected Indian language. Configuration is loaded from `.env` (`SARVAM_API_KEY` and optional `SALON_NAME`).

## Current status

The core demo flow is implemented, but there are no automated tests or deployment configuration in the repository. Treat it as a prototype rather than a production service.

