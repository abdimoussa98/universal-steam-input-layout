//! Button-owner transitions preserve each gesture's independent clock.
use super::{Control, Gestures, Phase, Recipe, sample::GestureSample};

pub(super) fn update(
    gestures: &mut Gestures,
    n: usize,
    recipe: &Recipe,
    sample: &GestureSample<'_>,
) {
    let control = Control::OWNERS[n];
    let down = sample.input.down(control);
    let was = sample.previous.down(control);
    if gestures.lanes[n].phase == Phase::Window
        && recipe.touch_cancels_window
        && sample.touched_release
    {
        gestures.enter(n, Phase::Idle, sample.now, None);
    }
    let phase = gestures.lanes[n].phase;
    if !down && was {
        release(gestures, n, recipe, sample);
    } else if down && !was && !matches!(phase, Phase::Combined | Phase::CombinedCover) {
        press(gestures, n, recipe, sample.now);
    }
    if down {
        consume_or_complete(gestures, n, recipe, sample);
    }
}

fn release(gestures: &mut Gestures, n: usize, recipe: &Recipe, sample: &GestureSample<'_>) {
    match gestures.lanes[n].phase {
        Phase::Pressed | Phase::Second => {
            gestures.enter(n, Phase::Window, sample.now, Some(recipe.window_ms));
            gestures.lanes[n].output_at_ms = Some(sample.now + recipe.output_ms);
        }
        Phase::Combined | Phase::CombinedCover => {
            gestures.enter(n, Phase::Idle, sample.now, None);
            if n < 2 && sample.input.down(Control::OWNERS[1 - n]) {
                gestures.enter(1 - n, Phase::Consumed, sample.now, None);
            }
        }
        _ => gestures.enter(n, Phase::Idle, sample.now, None),
    }
}

fn press(gestures: &mut Gestures, n: usize, recipe: &Recipe, now: u64) {
    // An opposite-owner press inside a timed window is a replacement output,
    // not a new modifier entry. Leave that window's own clock intact.
    let other_owner = gestures
        .lanes
        .iter()
        .enumerate()
        .any(|(j, lane)| j != n && lane.phase.page().is_some());
    if gestures.lanes[n].phase == Phase::Window {
        gestures.enter(n, Phase::Second, now, Some(recipe.cover_ms));
    } else if other_owner {
        gestures.enter(n, Phase::Output, now, None);
    } else {
        gestures.enter(n, Phase::Pressed, now, Some(recipe.hold_ms));
    }
}

fn consume_or_complete(
    gestures: &mut Gestures,
    n: usize,
    recipe: &Recipe,
    sample: &GestureSample<'_>,
) {
    let phase = gestures.lanes[n].phase;
    if matches!(phase, Phase::Pressed | Phase::Hold)
        && (sample
            .pressed
            .iter()
            .any(|c| recipe.cancel_controls.contains(c))
            || (recipe.both_sticks_consume && sample.input.sticks.iter().all(|b| *b)))
    {
        gestures.enter(n, Phase::Consumed, sample.now, None);
    } else if recipe.touch_completes && sample.touched_release {
        if phase == Phase::Pressed {
            gestures.enter(n, Phase::Hold, sample.now, None);
        } else if phase == Phase::Second {
            gestures.enter(n, Phase::Cover, sample.now, None);
        }
    }
}
