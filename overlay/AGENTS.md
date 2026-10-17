# Overlay development

These rules apply to the Rust overlay, browser viewer, and companion adapters.
Preserve controller mappings, gesture timing, serialization, diagnostic IDs, and
visible behavior when reorganizing code. Keep unrelated layout files untouched.

## Organization

- Keep every maintained Rust file at or below 400 physical lines, including tests
  and examples. Run `python3 overlay/scripts/check_rust_size.py` from the repo root.
- Clippy enforces a maximum of 60 function lines (excluding blank/comment lines),
  cognitive complexity 15, and five arguments including `self`.
- Split by responsibility: profiles, input, gestures, rendering, and platform
  transport. Avoid generic `utils`/`helpers` buckets and arbitrary numbered files.
- Keep types and implementations in the same domain module. A large type's
  implementation may use focused child modules in that domain.
- Keep `main.rs` and `lib.rs` focused on wiring. Keep implementation modules private;
  use `pub(super)` or `pub(crate)` internally and explicit public re-exports.
- Preserve the existing public API during refactors. Do not add blanket lint
  allowances or raise thresholds to pass. A necessary compatibility exception
  must use a narrowly scoped `#[expect(..., reason = "...")]`. The existing
  `InputTracker::sample_timed` signature is the sole argument-count exception.

## Validation

Run these from the repository root before finishing:

```sh
python3 overlay/scripts/check_rust_size.py
cargo fmt --manifest-path overlay/Cargo.toml -- --check
cargo clippy --locked --manifest-path overlay/Cargo.toml --all-targets --no-default-features -- -D warnings
cargo test --locked --manifest-path overlay/Cargo.toml --no-default-features
cargo clippy --locked --manifest-path overlay/Cargo.toml --all-targets --target wasm32-unknown-unknown --features web -- -D warnings
node --test overlay/scripts/test_downloads.mjs overlay/scripts/test_webhid.mjs
python3 -m unittest discover -s overlay/scripts -p 'test_*.py'
```

On Windows or macOS, also run strict Clippy and tests with `--features desktop`.
For viewer/input/rendering changes, build with `python3 overlay/scripts/build_web.py`,
run `wasm-pack test --headless --chrome overlay --no-default-features`, then
`python3 overlay/scripts/browser_smoke.py --bundle overlay/dist --webhid`.
Companion tests and browser checks need loopback networking. Browser checks need
matching Chrome/ChromeDriver; the smoke script accepts explicit executable paths.

The overlay workflow runs these gates before packaging; native adapter checks run
on their respective OS. Keep the matrix intact: a host-only or default-feature
Clippy invocation does not check browser or Windows code. Report unrun hardware
or platform checks explicitly. Do not claim simulated input proves hardware support.
