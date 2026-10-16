# Host the viewer with Dockge and GHCR

```text
Push to main → GitHub Actions tests/builds → GitHub Container Registry
Dockge deploy/update → pull the image from GHCR → serve port 18091
Existing HTTPS tunnel → http://SERVER_LAN_IP:18091 → viewer in your browser
```

The image contains Nginx and the static web bundle. GitHub publishes the image;
you deploy and update it through [Dockge](https://github.com/louislam/dockge).
The workflow uses GitHub-hosted runners and its built-in `GITHUB_TOKEN`.
No server API credentials, self-hosted runner, or Terraform is needed.

## First deployment

1. Commit and push these files to `main`. In **Actions → Keybind viewer**, wait
   for **Publish tested web image** to finish. You can also use **Run workflow**
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
5. For the wired Steam Controller on your Mac, follow the helper pairing steps
   below. Other browser-supported controllers can use the normal Gamepad API.

Use HTTPS for the public viewer so browser controller APIs are available.
Honor Nginx's `Cache-Control: no-cache` headers in your tunnel/cache settings,
so an update can load new HTML, JS and WASM rather than a cached bundle.

## Updating and choosing a version

Relevant pushes to `main` publish after all web, Windows and macOS checks pass.
Relevant paths include `overlay/**`, shared profile/export code, Ibex profile
sources and the viewer workflow. Pull requests run checks without publishing.
CI builds Linux amd64, saves the container tested in CI, and publishes that
same image without rebuilding it.

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

Your wired Steam Controller on macOS was not exposed by Brave's Gamepad API.
Moving the page into Docker does not change that. Pairing mode lets
the **hosted HTTPS page** use the same native controller reader that worked
locally. Steam is not required. Controller input travels directly from the local helper
to the browser; the hosted container only serves the web files.

Build the helper, or download `keybind-viewer-macos-helper` from the same
workflow. After extracting the downloaded artifact, run `chmod +x
keybind-overlay`. Start it with your actual viewer address:

```sh
./keybind-overlay --viewer-url https://YOUR_VIEWER_HOSTNAME/
```

For a source build, the equivalent executable is
`./overlay/target/release/keybind-overlay`. On Windows use
`keybind-overlay.exe --viewer-url https://YOUR_VIEWER_HOSTNAME/`.

Open the **complete pairing link printed by the helper**, in a browser on the
same computer as the controller. It opens the hosted page with a fragment
containing a random session token and loopback port. URL fragments are not
sent to Nginx, the tunnel or GHCR. The helper still listens only on `127.0.0.1`.
It allows API requests from the exact configured viewer origin and requires
the session token; arbitrary sites are refused. Input, trackpad positions,
timing and profile inheritance retain native-host authority.

Allow local network access if the browser asks. Chrome/Brave may require that
site permission; see [Chrome's local-network permission](https://developer.chrome.com/blog/local-network-access).
If denied, enable it in the site's permissions and reload. If the helper
restarts, open its newly printed pairing link. A plain visit without a pairing
link still uses the normal browser Gamepad API and manual reference mode.
Browser or organizational policies can block loopback access; the original
`--companion WEB_DIR` local-page mode remains available in that case.

The hosted HTTPS-to-loopback path is covered by the real Chrome smoke test,
including controls, trackpad/stick positions, timing, mode commands and helper
shutdown. CI uses synthetic native input. Local validation also passed in
Brave 155 with the physical Steam Controller: the HTTPS test page reported
`Live · Steam Controller · via helper`, accepted mode commands and detected
helper shutdown. The final public hostname still needs its first permission
grant and acceptance check; browser permission support is not universal. The
helper binary is updated separately from the web image, using the workflow's
Windows/macOS artifacts.

## Local validation

```sh
python3 -m unittest discover -s overlay/scripts -p 'test_*.py'
cargo test --locked --manifest-path overlay/Cargo.toml --features desktop
python3 overlay/scripts/build_web.py
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

To repeat the optional physical-controller check, use `--live-helper
overlay/target/debug/keybind-overlay --hosted-companion` instead of
`--companion-fixture`. This requires a connected controller. `--browser-binary`
can point to Brave; use a ChromeDriver version matching its Chromium version.
