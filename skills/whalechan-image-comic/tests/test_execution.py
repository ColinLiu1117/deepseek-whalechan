import unittest
import test_manage_run as fixtures

manage = fixtures.manage


class ExecutionTests(unittest.TestCase):


    def test_role_caps_survive_runtime_reduction(self):
        roles = manage.extension_module("agent_orchestration")
        policy = manage.role_execution({"batch_id": "test"})
        self.assertEqual(roles.targets(policy, 5, {"generation": 20, "collection": 2}),
                         {"planning": 0, "selection": 0, "generation": 3, "collection": 2, "delivery": 0})
        self.assertEqual(roles.targets(policy, 3, {"generation": 20, "collection": 2})["generation"], 2)
        self.assertEqual(policy["role_limits"]["planning"], 5)
        for slots in (0, 1, 2, 3, 4, 5, 6, 7, 10):
            result = roles.targets(policy, slots, {r: 20 for r in roles.ROLES}, "openai")
            self.assertLessEqual(sum(result.values()), slots)
        self.assertEqual(roles.capacity(3, "all-agents", 0), 2)
        self.assertEqual(roles.capacity(3, "subagents", 1), 2)
