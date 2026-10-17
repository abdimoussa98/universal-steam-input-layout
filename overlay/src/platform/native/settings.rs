use super::*;

#[derive(Default)]
pub(super) struct Options {
    pub(super) diagnostic: bool,
    pub(super) companion: Option<PathBuf>,
    pub(super) viewer_url: Option<String>,
    pub(super) profile: Option<PathBuf>,
    pub(super) device: Option<String>,
}
impl Options {
    pub(super) fn parse() -> Result<Self, String> {
        let mut opts = Self::default();
        let mut args = std::env::args().skip(1);
        while let Some(arg) = args.next() {
            match arg.as_str() {
            "--diagnostic"=>opts.diagnostic=true,
            "--viewer-url"=>opts.viewer_url=Some(args.next().ok_or("--viewer-url needs an HTTPS URL")?),
            "--companion"=>opts.companion=Some(args.next().ok_or("--companion needs the web bundle directory")?.into()),
            "--profile"=>opts.profile=Some(args.next().ok_or("--profile needs a JSON path")?.into()),
            "--device"=>opts.device=Some(args.next().ok_or("--device needs an SDL instance ID")?),
            "--help"|"-h"=>return Err("Usage: keybind-overlay [--profile FILE] [--companion WEB_DIR] [--viewer-url https://YOUR_VIEWER/] [--diagnostic] [--device SDL_ID]\nOpen the printed pairing link for hosted input. F1/F2/F3 select display modes. Ctrl+Alt+O recovers the interactive window.".into()),
            _=>return Err(format!("Unknown argument: {arg}")),
        }
        }
        Ok(opts)
    }
}

pub(super) struct LoadedSettings {
    settings_dir: PathBuf,
    preferences: Preferences,
    profile: Profile,
    error: Option<String>,
}
impl LoadedSettings {
    pub(super) fn load(profile_path: Option<PathBuf>) -> Result<Self, String> {
        let settings_dir = std::env::var_os("APPDATA")
            .map(PathBuf::from)
            .ok_or("APPDATA is unavailable")?
            .join("KeybindOverlay");
        let mut error = None;
        let preferences = match std::fs::read_to_string(settings_dir.join("preferences.json")) {
            Ok(json) => Preferences::parse(&json).unwrap_or_else(|e| {
                error = Some(e);
                Preferences::default()
            }),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Preferences::default(),
            Err(e) => {
                error = Some(e.to_string());
                Preferences::default()
            }
        };
        let profile_path = profile_path.unwrap_or_else(|| settings_dir.join("profile.json"));
        let profile = match std::fs::read_to_string(&profile_path) {
            Ok(json) => Profile::parse(&json).unwrap_or_else(|e| {
                error = Some(format!(
                    "{}: {e}; using bundled profile",
                    profile_path.display()
                ));
                Profile::parse(BUNDLED_PROFILE).expect("bundled profile")
            }),
            Err(e)
                if e.kind() == std::io::ErrorKind::NotFound
                    && profile_path == settings_dir.join("profile.json") =>
            {
                Profile::parse(BUNDLED_PROFILE).expect("bundled profile")
            }
            Err(e) => {
                error = Some(format!(
                    "{}: {e}; using bundled profile",
                    profile_path.display()
                ));
                Profile::parse(BUNDLED_PROFILE).expect("bundled profile")
            }
        };
        Ok(Self {
            settings_dir,
            preferences,
            profile,
            error,
        })
    }
}

pub(super) fn create_hub(
    opts: &mut Options,
    loaded: LoadedSettings,
    recovery_available: bool,
    keys: &mut Hotkeys<WinHotkeys>,
) -> Arc<Mutex<Hub>> {
    let registered = loaded.preferences.hotkeys;
    let conflicts = keys.rebind(registered);
    let device = opts.device.take();
    build_hub(loaded, device, recovery_available, conflicts)
}

fn build_hub(
    loaded: LoadedSettings,
    device: Option<String>,
    recovery_available: bool,
    conflicts: Vec<String>,
) -> Arc<Mutex<Hub>> {
    let LoadedSettings {
        settings_dir,
        preferences,
        profile,
        error,
    } = loaded;
    let registered = preferences.hotkeys;
    let digest = profile.digest();
    Arc::new(Mutex::new(Hub {
        data: FrameData {
            state: State::default(),
            profile,
            settings: HostSettings {
                selected: device,
                hotkeys: registered,
                devices: vec![],
                error: if conflicts.is_empty() {
                    None
                } else {
                    Some(conflicts.join("; "))
                },
            },
            preferences,
            native: true,
            remote: false,
            recovery_available,
            hud: false,
            companion_url: None,
            browser_connection: None,
            error,
        },
        sequence: 1,
        context: None,
        hidden: false,
        settings_dir,
        digest,
    }))
}
