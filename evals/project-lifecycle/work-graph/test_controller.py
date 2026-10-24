"""Behavioral checks of the isolated controller, with explicit simulated gates."""
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from controller import ARCHETYPES, Controller, Rejected, compile_plan, digest


def node(nid, needs=(), consumes=(), produces=(), op='ANALYZE', writes=()):
    return dict(id=nid, op=op, gate='fixture-verifier/v1', needs=list(needs),
                consumes=list(consumes), produces=list(produces), writes=list(writes))


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = [1000]
        self.c = Controller(self.temp.name, clock=lambda: self.now[0])
        self.plan = compile_plan([node('a', produces=['X']), node('b', consumes=['X'])])

    def init(self, **kwargs):
        self.c.init(self.plan, **kwargs)

    def reserve_start(self):
        aid = self.c.reserve('owner', self.c.show()['revision'])
        self.assertIsNotNone(aid)
        a = self.c.show()['attempts'][aid]
        self.assertTrue(self.c.start(aid, 'owner', a['inputs']))
        return aid

    def deliver(self, aid, event, candidate='candidate-A', verdict='pass'):
        a = self.c.show()['attempts'][aid]
        n = self.c.show()['plan']['nodes'][a['node']]
        self.c.complete(event, aid, candidate, verdict, {k: 'content' for k in n['produces']})

    def test_end_to_end_consumer_waits_and_success_is_explicit(self):
        self.init()
        with self.assertRaisesRegex(Rejected, 'undelivered'):
            self.c.finish()
        a = self.reserve_start()
        self.assertTrue(a.startswith('a:'))
        self.deliver(a, 'e1')
        b = self.reserve_start()
        self.assertTrue(b.startswith('b:'))
        self.assertEqual(self.c.show()['attempts'][b]['inputs']['X'], digest('content'))
        self.deliver(b, 'e2')
        self.assertTrue(self.c.finish())
        self.assertEqual(self.c.show()['outcome'], 'VERIFIED_SUCCESS')

    def test_two_next_calls_do_not_duplicate_dispatch(self):
        self.init()
        revision = self.c.show()['revision']
        self.assertIsNotNone(self.c.reserve('one', revision))
        with self.assertRaisesRegex(Rejected, 'CAS'):
            self.c.reserve('two', revision)
        self.assertIsNone(self.c.reserve('two', self.c.show()['revision']))
        self.assertEqual(self.c.show()['budget']['used'], 1)

    def test_concurrent_writers_cannot_both_reserve(self):
        self.init()
        revision = self.c.show()['revision']
        barrier = threading.Barrier(2)
        results = []

        def request():
            peer = Controller(self.temp.name, clock=lambda: self.now[0])
            barrier.wait()
            try:
                results.append(peer.reserve('worker', revision))
            except Rejected:
                results.append(None)

        threads = [threading.Thread(target=request) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(sum(r is not None for r in results), 1)
        self.assertEqual(self.c.show()['budget']['used'], 1)

    def test_duplicate_completion_is_idempotent_and_conflict_rejected(self):
        self.init()
        a = self.reserve_start()
        self.deliver(a, 'event')
        before = self.c.show()
        self.deliver(a, 'event')
        self.assertEqual(self.c.show(), before)
        with self.assertRaisesRegex(Rejected, 'payload changed'):
            self.deliver(a, 'event', candidate='different')
        self.assertEqual(self.c.show(), before)

    def test_replan_carries_budget_and_deliveries_and_revokes_packet(self):
        self.init()
        a = self.reserve_start()
        self.deliver(a, 'e1')
        b = self.c.reserve('owner', self.c.show()['revision'])
        packet = self.c.show()['attempts'][b]['inputs']
        used = self.c.show()['budget']['used']
        self.c.replan(self.plan, self.c.show()['revision'])
        self.assertEqual(self.c.show()['budget']['used'], used+1)
        self.assertIn(a, self.c.show()['deliveries'])
        with self.assertRaisesRegex(Rejected, 'reservation'):
            self.c.start(b, 'owner', packet)
        new_a = self.reserve_start()
        self.assertNotEqual(a, new_a)
        self.deliver(new_a, 'e2', candidate='candidate-B')
        self.assertEqual(self.c.show()['artifacts']['X']['version'], 2)

    def test_replan_cannot_reset_attempts_by_renaming(self):
        self.init()
        changed = compile_plan([node('new-a', produces=['X']), node('b', consumes=['X'])])
        before = self.c.show()
        with self.assertRaisesRegex(Rejected, 'lineage'):
            self.c.replan(changed, before['revision'])
        self.assertEqual(self.c.show(), before)

    def test_replan_cap_stops_instead_of_replenishing_budget(self):
        self.init(max_replans=1)
        self.c.replan(self.plan, self.c.show()['revision'])
        self.c.replan(self.plan, self.c.show()['revision'])
        self.assertEqual(self.c.show()['outcome'], 'BUDGET_EXHAUSTED')
        self.assertEqual(self.c.show()['replans'], 1)

    def test_repeated_failure_stops_even_after_replan(self):
        self.init()
        a = self.reserve_start()
        self.deliver(a, 'f1', verdict='fail')
        self.c.replan(self.plan, self.c.show()['revision'])
        a2 = self.reserve_start()
        self.deliver(a2, 'f2', candidate='candidate-B', verdict='fail')
        self.assertEqual(self.c.show()['outcome'], 'STALLED_SAME_FAILURE')
        with self.assertRaisesRegex(Rejected, 'not active'):
            self.c.finish()

    def test_inconsistent_verifier_on_same_input_blocks_promotion(self):
        self.init()
        a = self.reserve_start()
        self.deliver(a, 'fail', verdict='fail')
        a2 = self.reserve_start()
        self.deliver(a2, 'pass', verdict='pass')
        self.assertEqual(self.c.show()['outcome'], 'VERIFIER_UNSTABLE')
        self.assertNotIn('X', self.c.show()['artifacts'])

    def test_dispatch_and_verification_are_both_charged(self):
        self.init(units=1)
        a = self.reserve_start()
        self.deliver(a, 'e1')
        self.assertEqual(self.c.show()['budget']['used'], 1)
        self.assertEqual(self.c.show()['outcome'], 'BUDGET_EXHAUSTED')
        self.assertFalse(self.c.show()['deliveries'])

    def test_expired_and_wrong_holder_reservations_cannot_start(self):
        self.init()
        a = self.c.reserve('owner', self.c.show()['revision'])
        with self.assertRaises(Rejected):
            self.c.start(a, 'foreign', {})
        self.now[0] += 61
        self.assertFalse(self.c.start(a, 'owner', {}))
        self.assertEqual(self.c.show()['attempts'][a]['status'], 'revoked')

    def test_elapsed_deadline_and_clock_regression_fail_closed(self):
        self.init(seconds=5)
        self.now[0] += 6
        self.assertIsNone(self.c.reserve('owner', self.c.show()['revision']))
        self.assertEqual(self.c.show()['outcome'], 'BUDGET_EXHAUSTED')

    def test_clock_regression_is_not_extra_time(self):
        self.init()
        self.now[0] -= 1
        self.assertIsNone(self.c.reserve('owner', self.c.show()['revision']))
        self.assertEqual(self.c.show()['outcome'], 'ENVIRONMENT_BLOCKED')

    def test_resume_after_dispatch_never_blindly_redispatches(self):
        self.init()
        self.reserve_start()
        peer = Controller(self.temp.name, clock=lambda: self.now[0])
        peer.resume()
        self.assertEqual(peer.show()['outcome'], 'ENVIRONMENT_BLOCKED')
        self.assertEqual(len(peer.show()['attempts']), 1)

    def test_resume_revokes_pre_dispatch_reservation_without_refund(self):
        self.init()
        self.c.reserve('owner', self.c.show()['revision'])
        Controller(self.temp.name, clock=lambda: self.now[0]).resume()
        self.assertEqual(self.c.show()['budget']['used'], 1)
        self.assertEqual(self.c.show()['nodes']['a'], 'pending')

    def test_failed_atomic_replace_preserves_last_committed_record(self):
        self.init()
        before = self.c.path.read_bytes()
        with patch('controller.os.replace', side_effect=OSError('injected crash boundary')):
            with self.assertRaises(OSError):
                self.c.reserve('owner', self.c.show()['revision'])
        self.assertEqual(self.c.path.read_bytes(), before)
        self.assertTrue((Path(self.temp.name)/'work.pending').exists())
        self.c.resume()
        self.assertEqual(self.c.show()['attempts'], {})

    def test_scope_and_packet_mismatch_do_not_publish_output(self):
        self.init()
        a = self.reserve_start()
        with self.assertRaisesRegex(Rejected, 'scope'):
            self.c.complete('e', a, 'candidate', 'pass', {'X':'x'}, ['foreign.py'])
        self.assertFalse(self.c.show()['deliveries'])

    def test_tampered_plan_edges_cannot_bypass_compiler(self):
        broken = copy.deepcopy(self.plan)
        broken['edges']['b'] = []
        with self.assertRaisesRegex(Rejected, 'unvalidated'):
            self.c.init(broken)

    def test_stopped_run_cannot_be_reopened_by_replan(self):
        self.init(seconds=1)
        self.now[0] += 2
        self.c.reserve('owner', self.c.show()['revision'])
        before = self.c.show()
        with self.assertRaisesRegex(Rejected, 'not active'):
            self.c.replan(self.plan, before['revision'])
        self.assertEqual(before, self.c.show())

    def test_packet_input_must_equal_bound_artifact(self):
        self.init()
        a = self.reserve_start()
        self.deliver(a, 'e')
        b = self.c.reserve('owner', self.c.show()['revision'])
        with self.assertRaisesRegex(Rejected, 'stale packet'):
            self.c.start(b, 'owner', {'X': 'invented'})

    def test_persisted_plan_replans_with_non_alphabetic_independent_input(self):
        plan = compile_plan([node('z'), node('a')])
        self.c.init(plan)
        saved = self.c.show()
        self.c.replan(saved['plan'], saved['revision'])
        self.assertEqual(self.c.show()['graph_digest'], digest(plan))
        self.assertEqual(compile_plan([node('a'), node('z')]), plan)

    def test_resume_preserves_budget_exhaustion_with_running_attempt(self):
        self.init(units=1)
        a = self.reserve_start()
        self.deliver(a, 'e1')
        before = self.c.show()
        self.assertEqual(before['outcome'], 'BUDGET_EXHAUSTED')
        Controller(self.temp.name, clock=lambda: self.now[0]).resume()
        self.assertEqual(self.c.show(), before)


class CompilerTests(unittest.TestCase):
    def test_cycle_and_unresolved_consumer_are_rejected(self):
        with self.assertRaisesRegex(Rejected, 'cycle'):
            compile_plan([node('a', needs=['b']), node('b', needs=['a'])])
        with self.assertRaisesRegex(Rejected, 'unresolved'):
            compile_plan([node('a', consumes=['missing'])])

    def test_all_archetypes_accept_explicit_readonly_plan_but_forbid_writes_when_readonly(self):
        for archetype in sorted(ARCHETYPES):
            plan = compile_plan([node('a')], archetype)
            self.assertEqual(plan['order'], ['a'])
        for archetype in ('analysis_only','planning_only','review_only'):
            with self.assertRaisesRegex(Rejected, 'read-only'):
                compile_plan([node('a', op='CODE_PATCH', writes=['a.py'])], archetype)

    def test_invalid_operator_and_duplicate_producer_rejected(self):
        with self.assertRaises(Rejected):
            compile_plan([node('a',op='UNREGISTERED')])
        with self.assertRaisesRegex(Rejected,'producer'):
            compile_plan([node('a',produces=['X']),node('b',produces=['X'])])

    def test_compilation_does_not_modify_input_and_is_reproducible(self):
        source = [node('a', produces=['X']), node('b', consumes=['X'])]
        saved = copy.deepcopy(source)
        self.assertEqual(digest(compile_plan(source)), digest(compile_plan(source)))
        self.assertEqual(source, saved)


if __name__ == '__main__':
    unittest.main()
