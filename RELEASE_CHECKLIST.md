# Public release checklist

Use this checklist for every public source update.

## Scope

- [ ] The change is source, documentation, approved branding, or public tooling.
- [ ] No ROM, BIOS, emulator core, APK, AAB, signing material, archive, log, cache, or device capture is staged.
- [ ] New assets are original or legally redistributable and have a documented purpose.

## Privacy and security

- [ ] No production PIN, credential, token, private address, hostname, account, serial number, MAC address, or local user path is present.
- [ ] Android permissions and exported components were reviewed.
- [ ] Screenshots and reports contain only invented or manually sanitized state.
- [ ] PowerShell and Python public-release audits pass.
- [ ] Current and historical Git objects were checked when sensitive material may have entered a prior commit.

## Verification

- [ ] Pure Java catalog contract tests pass.
- [ ] Python audit tests pass.
- [ ] The Android debug build succeeds with temporary local configuration.
- [ ] Generated artifacts were removed from the repository tree.
- [ ] `PUBLIC_IMPORT_MANIFEST.json` was regenerated and validated.
- [ ] `git diff --check` passes and the staged diff was reviewed.

## Publication

- [ ] Version and changelog are current when behavior changed.
- [ ] Commit messages describe one logical change.
- [ ] The intended branch was pushed.
- [ ] The GitHub Public safety workflow completed successfully.
