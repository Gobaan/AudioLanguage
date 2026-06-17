import unittest

from learning_engine_scenarios import make_learning_state, plan_rows

HELLO_TARGET = "ja-target-respond-hi"
INTRODUCE_TARGET = "ja-target-my-name-is"
REPAIR_TARGET = "ja-target-i-dont-understand"
EXCUSE_ME_TARGET = "ja-target-excuse-me-attention"
FOOD_TARGET = "ja-target-one-local-food-please"

HELLO_ANCHOR = "ja-card-first-hi-dialogue-practice"
INTRODUCE_ANCHOR = "ja-card-introduce-self-dialogue-practice"
REPAIR_ANCHOR = "ja-card-dont-understand-dialogue-practice"
REPAIR_TRANSFER = "ja-card-repair-ticket-transfer-same_day_transfer"
EXCUSE_ME_ANCHOR = "ja-card-excuse-me-dialogue-practice"
EXCUSE_ME_DELAYED = "ja-card-excuse-me-station-review-delayed_review"
FOOD_ANCHOR = "ja-card-order-food-dialogue-practice"


class LearningEngineScenarioTests(unittest.TestCase):
    def test_fresh_learner_gets_three_new_anchor_lessons(self):
        with make_learning_state() as scenario:
            plan = scenario.build_plan_for()

        self.assertEqual(
            plan_rows(plan),
            [
                (HELLO_TARGET, "new", "new"),
                (INTRODUCE_TARGET, "new", "new"),
                (REPAIR_TARGET, "new", "new"),
            ],
        )

    def test_wrong_meaning_choice_produces_meaning_repair(self):
        with make_learning_state() as scenario:
            scenario.record_choice(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, is_correct=False)

            plan = scenario.build_plan_for()

        self.assertLessEqual(len(plan["lessons"]), 3)
        self.assertEqual(plan_rows(plan)[0], (HELLO_TARGET, "meaning_repair", "meaning_repair"))

    def test_later_spoken_success_clears_meaning_repair(self):
        with make_learning_state() as scenario:
            scenario.record_choice(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, is_correct=False)
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR)

            plan = scenario.build_plan_for(planning_date="2026-06-02")

        rows = plan_rows(plan)
        self.assertLessEqual(len(rows), 3)
        self.assertNotIn("meaning_repair", [purpose for _, purpose, _ in rows])
        self.assertEqual(rows[0], (HELLO_TARGET, "due_review", None))

    def test_failed_anchor_production_produces_recall_repair(self):
        with make_learning_state() as scenario:
            scenario.record_failed_anchor(target_id=INTRODUCE_TARGET, lesson_id=INTRODUCE_ANCHOR)

            plan = scenario.build_plan_for()

        self.assertLessEqual(len(plan["lessons"]), 3)
        self.assertEqual(plan_rows(plan)[0], (INTRODUCE_TARGET, "recall_repair", "recall_repair"))

    def test_passed_anchor_plus_failed_transfer_produces_transfer_repair(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=REPAIR_TARGET, lesson_id=REPAIR_ANCHOR)
            scenario.record_failed_transfer(target_id=REPAIR_TARGET, lesson_id=REPAIR_TRANSFER)

            plan = scenario.build_plan_for()

        self.assertLessEqual(len(plan["lessons"]), 3)
        self.assertEqual(plan_rows(plan)[0], (REPAIR_TARGET, "transfer_repair", "transfer_repair"))

    def test_passed_earlier_but_failed_delayed_review_produces_memory_repair(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=EXCUSE_ME_TARGET, lesson_id=EXCUSE_ME_ANCHOR)
            scenario.record_failed_delayed(target_id=EXCUSE_ME_TARGET, lesson_id=EXCUSE_ME_DELAYED)

            plan = scenario.build_plan_for()

        self.assertLessEqual(len(plan["lessons"]), 3)
        self.assertEqual(plan_rows(plan)[0], (EXCUSE_ME_TARGET, "memory_repair", "memory_repair"))

    def test_pending_unscored_attempt_is_neutral(self):
        with make_learning_state() as scenario:
            scenario.record_pending_attempt(target_id=FOOD_TARGET, lesson_id=FOOD_ANCHOR)

            plan = scenario.build_plan_for()

        self.assertLessEqual(len(plan["lessons"]), 3)
        self.assertNotIn("recall_repair", [purpose for _, purpose, _ in plan_rows(plan)])
        self.assertEqual(
            plan_rows(plan),
            [
                (HELLO_TARGET, "new", "new"),
                (INTRODUCE_TARGET, "new", "new"),
                (REPAIR_TARGET, "new", "new"),
            ],
        )

    def test_light_repair_load_allows_one_new_i_plus_one_anchor(self):
        with make_learning_state() as scenario:
            scenario.record_failed_anchor(target_id=INTRODUCE_TARGET, lesson_id=INTRODUCE_ANCHOR)

            plan = scenario.build_plan_for()

        rows = plan_rows(plan)
        self.assertLessEqual(len(rows), 3)
        self.assertEqual(rows[0], (INTRODUCE_TARGET, "recall_repair", "recall_repair"))
        self.assertEqual(rows[1:], [(HELLO_TARGET, "new", "new"), (REPAIR_TARGET, "new", "new")])

    def test_planner_returns_fewer_than_three_when_nothing_useful_exists(self):
        with make_learning_state() as scenario:
            for target_id, lesson_id in [
                (HELLO_TARGET, HELLO_ANCHOR),
                (INTRODUCE_TARGET, INTRODUCE_ANCHOR),
                (REPAIR_TARGET, REPAIR_ANCHOR),
                (EXCUSE_ME_TARGET, EXCUSE_ME_ANCHOR),
                (FOOD_TARGET, FOOD_ANCHOR),
            ]:
                scenario.record_passed_anchor(target_id=target_id, lesson_id=lesson_id)

            plan = scenario.build_plan_for(scene_set="delayed", planning_date="2026-06-02")

        rows = plan_rows(plan)
        self.assertLessEqual(len(rows), 3)
        self.assertTrue(rows)
        self.assertTrue(all(purpose == "due_review" for _, purpose, _ in rows))

    def test_repair_priority_matrix_and_due_review_before_new_content(self):
        with make_learning_state() as scenario:
            scenario.record_choice(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, is_correct=False)
            scenario.record_failed_anchor(target_id=INTRODUCE_TARGET, lesson_id=INTRODUCE_ANCHOR)
            scenario.record_passed_anchor(target_id=REPAIR_TARGET, lesson_id=REPAIR_ANCHOR)
            scenario.record_failed_transfer(target_id=REPAIR_TARGET, lesson_id=REPAIR_TRANSFER)
            scenario.record_passed_anchor(target_id=EXCUSE_ME_TARGET, lesson_id=EXCUSE_ME_ANCHOR)
            scenario.record_failed_delayed(target_id=EXCUSE_ME_TARGET, lesson_id=EXCUSE_ME_DELAYED)

            repair_plan = scenario.build_plan_for()

        self.assertEqual(
            [purpose for _, purpose, _ in plan_rows(repair_plan)],
            ["meaning_repair", "recall_repair", "transfer_repair"],
        )

        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR)

            due_review_plan = scenario.build_plan_for(planning_date="2026-06-02")

        due_review_rows = plan_rows(due_review_plan)
        self.assertEqual(due_review_rows[0], (HELLO_TARGET, "due_review", None))
        self.assertEqual(
            due_review_rows[1:],
            [(INTRODUCE_TARGET, "new", "new"), (REPAIR_TARGET, "new", "new")],
        )

    def test_first_spoken_pass_schedules_review_for_tomorrow(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, reviewed_at="2026-06-01")

            state = scenario.store.target_states("Bob", "ja")[HELLO_TARGET]

        self.assertEqual(state.review_count, 1)
        self.assertEqual(state.interval_days, 1)
        self.assertEqual(state.last_quality, 4)
        self.assertEqual(state.last_reviewed_at, "2026-06-01")
        self.assertEqual(state.next_review_at, "2026-06-02")

    def test_not_due_target_is_skipped_in_delayed_review(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, reviewed_at="2026-06-01")

            plan = scenario.build_plan_for(scene_set="delayed", planning_date="2026-06-01")

        self.assertEqual(plan_rows(plan), [])

    def test_due_target_appears_as_due_review(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, reviewed_at="2026-06-01")

            plan = scenario.build_plan_for(scene_set="delayed", planning_date="2026-06-02")

        self.assertEqual(plan_rows(plan), [(HELLO_TARGET, "due_review", None)])

    def test_next_day_review_waits_for_soft_minimum_gap_when_timestamps_exist(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(
                target_id=HELLO_TARGET,
                lesson_id=HELLO_ANCHOR,
                reviewed_at="2026-06-01T23:55:00",
            )

            plan = scenario.build_plan_for(scene_set="delayed", planning_date="2026-06-02T00:10:00")

        self.assertEqual(plan_rows(plan), [])

    def test_next_day_review_is_due_after_soft_minimum_gap(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(
                target_id=HELLO_TARGET,
                lesson_id=HELLO_ANCHOR,
                reviewed_at="2026-06-01T23:55:00",
            )

            plan = scenario.build_plan_for(scene_set="delayed", planning_date="2026-06-02T08:00:00")

        self.assertEqual(plan_rows(plan), [(HELLO_TARGET, "due_review", None)])

    def test_repeated_passes_grow_review_interval(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, reviewed_at="2026-06-01")
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, reviewed_at="2026-06-02")

            state = scenario.store.target_states("Bob", "ja")[HELLO_TARGET]

        self.assertEqual(state.review_count, 2)
        self.assertEqual(state.interval_days, 3)
        self.assertEqual(state.next_review_at, "2026-06-05")

    def test_failure_after_previous_pass_increments_lapse_and_shortens_schedule(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, reviewed_at="2026-06-01")
            scenario.record_failed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, reviewed_at="2026-06-02")

            state = scenario.store.target_states("Bob", "ja")[HELLO_TARGET]
            plan = scenario.build_plan_for(planning_date="2026-06-02")

        self.assertEqual(state.lapse_count, 1)
        self.assertEqual(state.interval_days, 1)
        self.assertEqual(state.last_quality, 0)
        self.assertEqual(state.next_review_at, "2026-06-03")
        self.assertEqual(plan_rows(plan)[0], (HELLO_TARGET, "recall_repair", "recall_repair"))

    def test_pending_attempt_does_not_change_review_schedule(self):
        with make_learning_state() as scenario:
            scenario.record_passed_anchor(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, reviewed_at="2026-06-01")
            scenario.record_pending_attempt(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR)

            state = scenario.store.target_states("Bob", "ja")[HELLO_TARGET]

        self.assertEqual(state.review_count, 1)
        self.assertEqual(state.interval_days, 1)
        self.assertEqual(state.next_review_at, "2026-06-02")

    def test_multiple_choice_does_not_update_review_interval(self):
        with make_learning_state() as scenario:
            scenario.record_choice(target_id=HELLO_TARGET, lesson_id=HELLO_ANCHOR, is_correct=True)

            state = scenario.store.target_states("Bob", "ja")[HELLO_TARGET]

        self.assertEqual(state.review_count, 0)
        self.assertEqual(state.interval_days, 0)
        self.assertEqual(state.next_review_at, "")

    def test_no_participant_plan_still_returns_legacy_full_plan(self):
        with make_learning_state() as scenario:
            plan = scenario.build_plan_for(participant_id=None, order_seed="legacy")

        self.assertEqual(plan["plan_version"], 1)
        self.assertEqual(plan["session_id"], "ja:mvp:legacy")
        self.assertGreater(len(plan["lessons"]), 3)
        self.assertTrue(all("planPurpose" not in lesson for lesson in plan["lessons"]))

    def test_synthetic_state_does_not_require_validation_sessions_or_recordings(self):
        with make_learning_state() as scenario:
            scenario.record_failed_anchor(target_id=INTRODUCE_TARGET, lesson_id=INTRODUCE_ANCHOR)
            states = scenario.store.target_states("Bob", "ja")

            plan = scenario.build_plan_for()

        self.assertIn(INTRODUCE_TARGET, states)
        self.assertEqual(plan_rows(plan)[0], (INTRODUCE_TARGET, "recall_repair", "recall_repair"))


if __name__ == "__main__":
    unittest.main()
