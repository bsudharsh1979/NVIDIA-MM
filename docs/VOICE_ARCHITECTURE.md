# Voice architecture

`VoiceProvider` adapters:

- `ElevenLabsVoiceProvider` — default premium TTS when keyed
- `SarvamVoiceProvider` — Indic speech; keep NVIDIA English terminology
- `OpenAIRealtimeVoiceProvider` — barge-in / interruption interface

Voice is optional. App startup does not require any of these keys. Interruption is specified as cancel-and-reprompt on the realtime adapter; Demo mode is text-only.
