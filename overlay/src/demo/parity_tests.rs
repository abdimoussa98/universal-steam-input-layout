use super::{Engine, Input, Layout};

#[derive(serde::Deserialize)]
struct Trace {
    controller: String,
    variant: String,
    name: String,
    steps: Vec<Step>,
}
#[derive(serde::Deserialize)]
struct Step {
    at: u64,
    control: String,
    down: bool,
    stack: Vec<String>,
    outputs: Vec<String>,
    typed: Vec<String>,
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn python_scenario_traces_match_rust_and_wasm() {
    let catalog = Layout::catalog().unwrap();
    let traces: Vec<Trace> =
        serde_json::from_str(include_str!("../../tests/fixtures/demo-traces.json")).unwrap();
    for trace in traces {
        let layout = catalog
            .iter()
            .find(|l| l.controller == trace.controller && l.variant == trace.variant)
            .unwrap()
            .clone();
        let mut e = Engine::new(layout);
        for step in trace.steps {
            e.advance_to(step.at);
            if !step.control.is_empty() {
                e.input(&Input::Button {
                    control: step.control.clone(),
                    down: step.down,
                });
            }
            let context = format!(
                "{} {} {} at {} {}",
                trace.controller, trace.variant, trace.name, step.at, step.control
            );
            assert!(e.error.is_none(), "{context}: {:?}", e.error);
            assert_eq!(e.stack_titles(), step.stack, "{context}");
            assert_eq!(
                e.output.down.iter().cloned().collect::<Vec<_>>(),
                step.outputs,
                "{context}"
            );
            let typed: Vec<_> = e
                .output
                .events
                .iter()
                .filter(|event| matches!(event.kind.as_str(), "down" | "tap"))
                .map(|event| event.detail.clone())
                .collect();
            assert_eq!(typed, step.typed, "{context}");
        }
    }
}
