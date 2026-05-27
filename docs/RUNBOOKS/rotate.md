# Sandbox Pilot · Secrets rotation

## Inference backend keys (e.g. cloud LLM provider)

1. Generate new key with the provider
2. Append to your secrets store (axegate.json or env)
3. `SANDBOXPILOT_INFERENCE_KEY=<new> sandboxpilot serve --config pilot.toml`
4. Verify with `sandboxpilot health`
5. After 24h grace, revoke the old key with the provider

## Knox archive signing key (axe-keep)

The Knox key is the root of all artifact attestation. Rotation is breaking
unless we use the soft-rotation schema (multiple valid keys per manifest).

**Soft rotation (preferred):**
1. Generate new keypair: `python3 -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; ..."`
2. Append to `manifest.json` → `signing_keys[]` array (active_since=now)
3. New artifacts signed with new key; old artifacts still verify against old key
4. Old key marked `active_until` when fully retired

**Hard rotation (compromise scenario):**
1. New keypair
2. Re-sign ALL artifacts under the new key
3. Mark old key as REVOKED in manifest
4. Public broadcast on observer announcing the rotation
