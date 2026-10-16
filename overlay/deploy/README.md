# Host the viewer with Dockge and GHCR

```text
Push to main → GitHub Actions builds → GitHub Container Registry
Dockge deploy/update → pull the image from GHCR → serve port 18091
Existing HTTPS tunnel → http://SERVER_LAN_IP:18091 → viewer in your browser
```

The image contains Nginx and the static web bundle. GitHub publishes the image;
you deploy and update it through [Dockge](https://github.com/louislam/dockge).
The workflow uses GitHub-hosted runners and its built-in `GITHUB_TOKEN`.
No server API credentials, self-hosted runner, or Terraform is needed.

## First deployment

1. Commit and push these files to `main`. In **Actions → Keybind viewer**, wait
   for **Publish web image** to finish. You can also use **Run workflow**
   on `main`. The summary supplies your image reference:
   `ghcr.io/<owner>/<repository>-web:latest` (all lowercase).
2. On GitHub, open the new package's **Package settings → Change visibility**
   and select **Public**. GHCR packages start private; a public container image
   can be pulled without a login. The repository can remain private. See
   [GitHub package visibility](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).
3. In Dockge, create a stack named `keybind-viewer`, paste
   [compose.yaml](compose.yaml), and replace the example `image:` with the
   reference from step 1. Deploy the stack. No source checkout or build on the
   server is needed.
4. Open `http://SERVER_LAN_IP:18091` to check the page. Point your existing
   HTTPS tunnel at that address and use the HTTPS hostname in your browser.
   If the tunnel runs in a separate container, use a reachable server address;
   `localhost` would mean the tunnel container. Change host port `18091` in
   Compose if it is already occupied; the container listens on `8080`.
5. Plug the Steam Controller 2 or its wireless receiver into your computer,
   click **Connect controller** in the viewer, and select it in the browser picker. No local
   helper or Steam installation is required for this connection.

Use HTTPS for the public viewer so browser controller APIs are available.
Honor Nginx's `Cache-Control: no-cache` headers in your tunnel/cache settings,
so an update can load new HTML, JS and WASM rather than a cached bundle.

## Updating and choosing a version

Relevant pushes to `main` publish after the web bundle and container build.
Relevant paths include `overlay/**`, shared profile/export code, Ibex profile
sources and the viewer workflow. Pull requests build without publishing.
The viewer pipeline skips tests, browser/container smoke tests, formatting
checks and Clippy. Windows/macOS helper builds run independently and do not
block publishing the web image. CI builds Linux amd64, saves the container,
and publishes that same image without rebuilding it. Tests remain available
for local runs using the commands below.

Each release has a full commit SHA tag and an immutable `@sha256:...` digest.
The current `main` release also updates `:latest`; an older workflow cannot
move that tag back over a newer release. Image references appear in the
publish job summary.

After publication, use Dockge's stack image update action to pull the image
and recreate the container. **Publishing alone does not update a running
stack.** From the stack directory, the equivalent Compose commands are:

```sh
docker compose pull
docker compose up -d
```

Refresh the browser to load the new viewer. To pin a release or roll back,
replace the Compose `image:` with a previous successful run's
`ghcr.io/<owner>/<repository>-web@sha256:<digest>` and redeploy. Keep those
images in GHCR if you want to return to them later.

## Steam Controller in the hosted browser

Open the HTTPS viewer in a desktop browser with WebHID enabled. Click
**Connect controller** and choose your Steam Controller 2 or its wireless
receiver in the browser's permission dialog. The viewer selects a controller automatically. It reads
buttons, triggers, sticks, capacitive stick touches and trackpad positions
straight from USB, then feeds the same Rust bindings and gesture engine.
Controller input stays on your computer; the container only serves static files.

The direct connection supports the wired Valve `28de:1302` Triton/Ibex
controller and the `28de:1304` (Proteus) / `28de:1305` (Nereid) wireless
receivers. Other controllers still use the normal Gamepad API: press a button
and select the controller under Settings. Bluetooth and original Steam
Controller HID protocols are not claimed by this decoder.

For wireless input, use a controller already paired with the receiver. The
viewer listens to the receiver's controller interfaces and follows the first
active slot. It supports one controller at a time and retains that slot when
the controller powers off or the receiver is unplugged. To choose another
controller, use **Disconnect controller**, turn off other controllers, and
connect again. The receiver can stay connected while waiting for its controller;
held controls and timers clear immediately on a radio disconnect report.
The viewer does not change pairing or update controller firmware.

If no picker appears, enable HID device requests in the browser's site/device
permissions and try again. Cancelling the dialog leaves the viewer disconnected.
If the browser does not provide WebHID or the page is insecure, the viewer
explains the missing capability. Chrome and Edge provide desktop WebHID;
Brave must allow the site's HID requests. See
[WebHID permissions](https://developer.chrome.com/docs/capabilities/hid).
A permission grant cannot expose an interface blocked by the browser or OS.

Unplugging or stalled input clears held controls and timers. Reconnecting the
same authorized device can resume input; otherwise click **Connect controller**
again. **Disconnect controller** closes USB access. Background tabs pause the
viewer and resume only from a fresh report. The browser temporarily disables
the controller's desktop mouse emulation while connected, matching SDL's
transient setting; the controller restores it when the connection stops.

The browser transport handles permissions and raw reports. Decoding and all
binding/timing logic remain in Rust. The local browser smoke test exercises
the real WASM app with synthetic USB input, including cancellation, denied
permissions, quick tap edges, coordinates, unplug/reconnect and stale input.
Receiver tests also cover unused slots, controller power-off/on and isolation
from other active controllers. Physical wired input was confirmed by the user
in Brave on macOS and Flatpak Chrome on Bazzite. Wireless receiver acceptance
still needs a physical check on the target computer/browser.

### Optional native companion

The older native companion remains available for existing desktop users. It
is optional for direct USB browser input. Its usage is documented in the
[viewer README](../README.md#optional-macos-companion-steam-not-required).

## Local validation

```sh
python3 -m unittest discover -s overlay/scripts -p 'test_*.py'
node --test overlay/scripts/test_webhid.mjs
cargo test --locked --manifest-path overlay/Cargo.toml --features desktop
python3 overlay/scripts/build_web.py
python3 overlay/scripts/browser_smoke.py --bundle overlay/dist --webhid
cargo build --locked --manifest-path overlay/Cargo.toml --features desktop --example companion_fixture
python3 overlay/scripts/browser_smoke.py --bundle overlay/dist \
  --companion-fixture overlay/target/debug/examples/companion_fixture --hosted-companion
python3 overlay/scripts/release_manifest.py --bundle overlay/dist --revision "$(git rev-parse HEAD)"
docker build -f overlay/deploy/Dockerfile -t keybind-viewer:test overlay
```

The smoke test needs ChromeDriver/Chrome (paths can be passed explicitly) and
OpenSSL. It creates a temporary HTTPS certificate/profile, accepts that test
certificate only, and leaves browser CORS/mixed-content protections enabled.
These tests run locally without publishing an image or updating a server.

To repeat the optional native-companion hardware check, use `--live-helper
overlay/target/debug/keybind-overlay --hosted-companion` instead of
`--companion-fixture`. This requires a connected controller. `--browser-binary`
can point to Brave; use a ChromeDriver version matching its Chromium version.
