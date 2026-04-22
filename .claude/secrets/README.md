# Secrets — gitignored, never committed

This directory holds local-only secret material. Everything except this README is
gitignored (see `.gitignore`).

## `mcomzos-ota.key`

The **private** RSA signing key for RAUC OTA bundles. The matching **public**
cert is committed to `src/ota/keyring.pem` and baked into every image.

**Before the first OTA release:**

1. Copy the contents of `mcomzos-ota.key` to a GitHub Actions secret named
   `OTA_SIGNING_KEY` on this repo:
   ```
   gh secret set OTA_SIGNING_KEY < .claude/secrets/mcomzos-ota.key
   ```
2. Keep an offline backup of `mcomzos-ota.key` somewhere safe (password
   manager, USB key in a safe). If this key is lost, we can't sign further
   updates — every deployed device would need reflashing to accept a new
   keyring.
3. If the key is compromised (leaked), rotate: generate a new keypair, ship a
   release that installs the new public cert in `/etc/rauc/keyring.pem`,
   signed with the *old* key. After that release propagates, the old key is
   safe to revoke.

Do not commit this file. Do not paste it into chat. Do not push it.
