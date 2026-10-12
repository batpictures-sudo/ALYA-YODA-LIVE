# ALYA-YODA-LIVE

Low-latency neural Yoda voice streaming project for Alya.

## Architecture
- GitHub Actions: public CI, build and remote-control tests only
- Unikraft Cloud: intended persistent runtime
- Chrome bridge: streaming audio client
- GrandMasterYoda RVC: neural voice conversion target

## Non-negotiable requirements
- no wait for a complete WAV before playback
- low-latency chunked/streaming audio
- no heavy neural compute on the event laptop
- no secrets committed to this public repository
- zero-cost path only

This repository intentionally starts with a CI smoke test before any cloud secret is added.
