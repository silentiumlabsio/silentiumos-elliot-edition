# Fire OS Limitations

On the tested Fire OS 7 device:

- Amazon Home packages are protected and cannot be disabled through ordinary ADB shell privileges.
- Third-party home assignment may report success without replacing Amazon Home consistently.
- SilentiumOS uses accessibility-based redirection and a foreground guard service.
- A brief Amazon Home screen can appear before SilentiumOS returns.
- This project does not claim bootloader unlocking, custom firmware replacement, or unsupported root access.

Behavior can differ across Fire TV generations and Fire OS updates. Test on owned hardware and preserve a recovery path to Amazon Home.
