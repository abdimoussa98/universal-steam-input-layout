use super::{Engine, Layout};
use std::collections::BTreeSet;

#[derive(serde::Deserialize)]
struct Expectations {
    controller: String,
    variant: String,
    sha256: String,
    controls: Vec<String>,
    answers: Vec<Vec<Option<(usize, usize)>>>,
    cases: Vec<(Vec<usize>, usize)>,
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn every_layer_resolves_inheritance_like_the_source_layout_audit() {
    let catalog = Layout::catalog().unwrap();
    let fixtures: Vec<Expectations> =
        serde_json::from_str(include_str!("../../tests/fixtures/demo-inheritance.json")).unwrap();
    assert_eq!(fixtures.len(), catalog.len());
    for fixture in fixtures {
        let layout = catalog
            .iter()
            .find(|l| l.controller == fixture.controller && l.variant == fixture.variant)
            .unwrap();
        assert_eq!(layout.sha256, fixture.sha256);
        let mut engine = Engine::new(layout.clone());
        let mut seen = BTreeSet::new();
        for (stack, answer) in fixture.cases {
            seen.extend(stack.iter().copied());
            engine.stack = stack;
            assert_eq!(fixture.controls.len(), fixture.answers[answer].len());
            for (control, expected) in fixture.controls.iter().zip(&fixture.answers[answer]) {
                assert_eq!(
                    engine.binding(control).0,
                    *expected,
                    "{} {:?} {control}",
                    layout.label(),
                    engine.stack_titles()
                );
            }
        }
        assert_eq!(
            seen,
            (0..layout.layers.len()).collect(),
            "Every declared layer must have inheritance coverage: {}",
            layout.label()
        );
    }
}
