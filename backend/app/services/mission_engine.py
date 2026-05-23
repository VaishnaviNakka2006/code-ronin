from typing import Dict, Any, List

from app.db import supabase
from app.services.execution.subprocess_runner import SubprocessRunner


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

        # Fetch test cases from Supabase
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

            # Test input code from DB
            test_input = tc.get(
                "input",
                ""
            )

            # Combine user solution + test execution
            full_code = (
                user_code
                + "\n\n"
                + test_input
            )

            # Execute code
            actual_output = (
                SubprocessRunner.execute(
                    full_code
                )
            )

            actual_output = str(
                actual_output
            ).strip()

            passed_flag = (
                actual_output == expected
            )

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