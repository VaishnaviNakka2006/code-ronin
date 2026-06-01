from typing import Dict, Any, List

from app.db import supabase
from app.config import USE_DOCKER

if USE_DOCKER:
    from app.services.execution.docker_runner import DockerRunner
    _runner = DockerRunner()
else:
    from app.services.execution.subprocess_runner import SubprocessRunner
    _runner = SubprocessRunner()


class MissionEngine:

    @staticmethod
    def _format_details(details: List[Dict]) -> str:
        lines = []

        for d in details:
            status = "✓" if d["passed"] else "✗"

            lines.append(
                f"{status} Test {d['test_id']}: "
                f"expected '{d['expected']}', "
                f"got '{d['actual']}'"
            )

        return "\n".join(lines)

    @staticmethod
    def run_tests(
        mission_id: int,
        user_code: str
    ) -> Dict[str, Any]:

        res = (
            supabase
            .table("test_cases")
            .select("*")
            .eq("mission_id", mission_id)
            .execute()
        )

        test_cases = res.data

        if not test_cases:
            return {
                "success": False,
                "score": 0,
                "tests_passed": 0,
                "total_tests": 0,
                "output": "No test cases defined.",
                "details": []
            }

        passed = 0
        total = len(test_cases)

        total_weight = sum(
            tc.get("weight", 1.0)
            for tc in test_cases
        )

        earned_weight = 0.0

        details = []

        for tc in test_cases:

            test_id = tc["id"]

            expected = str(
                tc["expected_output"]
            ).strip()

            test_input = tc.get(
                "input",
                ""
            )

            try:

                # =====================
                # MISSION 3 - FACTORIAL
                # =====================
                if mission_id == 3:

                    local_vars = {}

                    exec(user_code, local_vars, local_vars)

                    func = local_vars.get("factorial")

                    if not func:

                        actual_output = "Function factorial() not found"

                        passed_flag = False

                    else:

                        result = func(int(test_input))

                        actual_output = str(result).strip()

                        passed_flag = (
                            actual_output == expected
                        )

                # =====================
                # OTHER MISSIONS
                # =====================
                else:

                    result = _runner.execute(
                        code=user_code,
                        stdin_input=test_input
                    )

                    actual_output = str(result).strip()

                    passed_flag = (
                        actual_output == expected
                    )

            except Exception as e:

                actual_output = str(e)

                passed_flag = False

            if passed_flag:

                passed += 1

                earned_weight += tc.get(
                    "weight",
                    1.0
                )

            details.append({

                "test_id": test_id,

                "passed": passed_flag,

                "expected": expected,

                "actual": actual_output,

                "description": tc.get(
                    "description",
                    ""
                )
            })

        score = (
            earned_weight / total_weight
            if total_weight > 0
            else 0
        )

        all_passed = (
            score >= 1.0
        )

        return {

            "success": all_passed,

            "score": score,

            "tests_passed": passed,

            "total_tests": total,

            "output": MissionEngine._format_details(
                details
            ),

            "details": details
        }