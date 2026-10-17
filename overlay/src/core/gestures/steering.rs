//! Direction gestures active while exactly one steering modifier is held.
use super::{Control, Gestures, Lane, Phase, SteeringProfile, sample::GestureSample};

pub(super) fn update(gestures: &mut Gestures, sample: &GestureSample<'_>) {
    let Some(recipe) = sample
        .profile
        .steering
        .as_ref()
        .filter(|_| sample.mode == super::Mode::Steering)
    else {
        return;
    };
    if sample.input.down(Control::L1) == sample.input.down(Control::R1) {
        gestures.steering_lane = Lane::default();
        gestures.steering_direction = 0;
        return;
    }
    let direction = direction(sample.input.stick_positions[0], recipe.deadzone);
    advance(&mut gestures.steering_lane, sample.now);
    if direction == 0 {
        release(&mut gestures.steering_lane, recipe, sample.now);
    } else if direction != gestures.steering_direction
        || matches!(gestures.steering_lane.phase, Phase::Idle | Phase::Window)
    {
        press(gestures, direction, recipe, sample.now);
    }
    // A consumed direction applies Tap Cover without dropping its inherited modifier.
    if gestures.steering_lane.phase == Phase::Pressed
        && (sample
            .pressed
            .iter()
            .any(|c| !matches!(c, Control::L1 | Control::R1))
            || sample.touched_release)
    {
        gestures.steering_lane.phase = Phase::Hold;
        gestures.steering_lane.deadline_ms = None;
    }
}

fn direction(position: Option<[i16; 2]>, deadzone: i16) -> i8 {
    position.map_or(0, |[x, y]| {
        if y.unsigned_abs() > deadzone as u16 && y.unsigned_abs() >= x.unsigned_abs() {
            if y < 0 { -1 } else { 1 }
        } else {
            0
        }
    })
}

fn advance(lane: &mut Lane, now: u64) {
    if lane.deadline_ms.is_some_and(|t| now >= t) {
        lane.phase = match lane.phase {
            Phase::Pressed => Phase::Hold,
            Phase::Second => Phase::Cover,
            _ => Phase::Idle,
        };
        lane.deadline_ms = None;
    }
}

fn release(lane: &mut Lane, recipe: &SteeringProfile, now: u64) {
    if matches!(lane.phase, Phase::Pressed | Phase::Second) {
        *lane = Lane {
            phase: Phase::Window,
            started_ms: now,
            deadline_ms: Some(now + recipe.window_ms),
            ..Lane::default()
        };
    } else if lane.phase != Phase::Window {
        *lane = Lane::default();
    }
}

fn press(gestures: &mut Gestures, direction: i8, recipe: &SteeringProfile, now: u64) {
    let second =
        direction == gestures.steering_direction && gestures.steering_lane.phase == Phase::Window;
    gestures.steering_lane = Lane {
        phase: if second {
            Phase::Second
        } else {
            Phase::Pressed
        },
        started_ms: now,
        deadline_ms: Some(
            now + if second {
                recipe.cover_ms
            } else {
                recipe.hold_ms
            },
        ),
        ..Lane::default()
    };
    gestures.steering_direction = direction;
}
