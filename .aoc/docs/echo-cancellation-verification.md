# WebRTC Echo Cancellation Verification

## Date: 2026-03-25

## Summary

Verified and explicitly configured WebRTC echo cancellation (AEC) in the
Agent On Call frontend. All three audio processing constraints are now
explicitly set in the `LiveKitRoom` component.

## Findings

### LiveKit SDK Defaults

The `livekit-client` SDK (installed version) has built-in audio defaults at
`livekit-client/dist/livekit-client.esm.mjs:17245`:

```javascript
const audioDefaults = {
  deviceId: { ideal: 'default' },
  autoGainControl: true,
  echoCancellation: true,
  noiseSuppression: true,
  voiceIsolation: true,
};
```

When `audio={true}` is passed to `LiveKitRoom`, the SDK applies these defaults
via `mergeDefaultOptions()`. So echo cancellation WAS already enabled by default.

### What We Changed

Changed `audio={true}` to explicit constraints in both `page.tsx` and
`test/page.tsx`:

```tsx
audio={{
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
}}
```

This makes the configuration explicit and self-documenting. The LiveKit SDK
will merge these with its own defaults (adding `deviceId` and `voiceIsolation`).

### Backend VAD Configuration

The backend uses Silero VAD (in `turn_taking.py`) with:
- `activation_threshold: 0.55` (slightly above default 0.5)
- `min_silence_duration: 0.8s` (above default 0.55s)

These conservative settings help prevent the agent's TTS output from being
picked up as user speech, complementing the frontend AEC.

### Browser Compatibility

WebRTC AEC is supported in all modern browsers:
- Chrome: Excellent AEC via WebRTC (uses platform AEC)
- Firefox: Good AEC support (uses RNNoise + platform AEC)
- Safari: AEC supported since Safari 11+
- Edge: Same engine as Chrome

LiveKit's SDK additionally handles Firefox-specific constraint remapping
(`noiseSuppression` -> `mozNoiseSuppression`) automatically.

### LiveKit Server-Side

LiveKit server does not perform additional AEC -- it relies on the client-side
WebRTC AEC. This is standard practice. The LiveKit Agents framework on the
backend uses server-side VAD (Silero) to detect speech, which is separate from
the client's echo cancellation.

## Recommendations

1. The current configuration is correct for most use cases
2. Users with speaker setups (no headphones) should work fine with browser AEC
3. If echo issues are reported on specific hardware, the `voiceIsolation`
   constraint (experimental, from LiveKit defaults) provides additional
   suppression on supported browsers
4. The VAD tuning in `turn_taking.py` provides a secondary layer of protection
   against echo-triggered false positives
