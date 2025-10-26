"""
This module contains the scheduled job for automatically promoting
the winning variant of an A/B test.
"""

from sqlalchemy.orm import Session
from ..database import get_db
from ..services.ab_testing_service import ABTestingService
from ..services.statistical_service import StatisticalService


def run_auto_promote_winner_job():
    """
    This job finds running A/B tests with auto-promotion enabled,
    checks for a statistically significant winner, and promotes the
    winner automatically.
    """
    print("Starting auto-promote winner job...")
    db: Session = next(get_db())

    try:
        ab_testing_service = ABTestingService(db, None)
        statistical_service = StatisticalService(db)

        # Get all running A/B tests with auto-promote enabled
        tests_to_check = ab_testing_service.get_running_auto_promote_tests()

        if not tests_to_check:
            print("No running A/B tests with auto-promotion enabled found.")
            return

        for test in tests_to_check:
            print(f"Checking A/B test #{test.id} for a winner...")

            # Check for a statistically significant winner
            winner_variant = statistical_service.get_statistically_significant_winner(
                test_id=test.id
            )

            if winner_variant:
                print(
                    f"Winner found for test #{test.id}: Variant #{winner_variant.id}. Promoting..."
                )
                try:
                    # Promote the winner
                    ab_testing_service.promote_winner(
                        test_id=test.id, winner_variant_id=winner_variant.id
                    )
                    print(
                        f"Successfully promoted variant #{winner_variant.id} for test #{test.id}."
                    )
                except Exception as e:
                    print(f"Error promoting winner for test #{test.id}: {e}")
            else:
                print(f"No statistically significant winner yet for test #{test.id}.")

    finally:
        print("Auto-promote winner job finished.")
        db.close()


if __name__ == "__main__":
    run_auto_promote_winner_job()
