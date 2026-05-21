# Rummikub App

Flutter Android app — Rummikub assistant (simulation + optimal moves).

## Setup

1. Install [Flutter](https://docs.flutter.dev/get-started/install) and Android SDK.
2. From this folder:

```bash
flutter pub get
flutter analyze
flutter test
flutter run
```

## MVP (phases 1–8)

- Simulate legal rack + table
- Find and show all optimal moves (max tiles from rack)
- First-meld toggle (30+ points)
- Step-by-step explanation per move (play + table reorganize)
- Restore last session via Hive on app restart
- Light / dark theme

## Next (future)

- Camera / tile recognition (`features/vision/`)
