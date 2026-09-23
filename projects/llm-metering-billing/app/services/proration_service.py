from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass(frozen=True)
class ProrationResult:
    current_plan_code: str
    target_plan_code: str
    cycle_total_seconds: int
    cycle_elapsed_seconds: int
    cycle_remaining_seconds: int
    current_plan_price_cents: int
    target_plan_price_cents: int
    unused_credit_cents: int
    prorated_charge_cents: int
    net_charge_cents: int
    net_charge_usd: str


class ProrationService:
    """
    Computes exact integer financial proration for mid-cycle subscription changes.
    Guarantees no fractional cent leakage using standard integer arithmetic.
    """

    @staticmethod
    def calculate_mid_cycle_proration(
        period_start: datetime,
        period_end: datetime,
        upgrade_time: datetime,
        current_price_cents: int,
        target_price_cents: int,
        current_plan_code: str = "free",
        target_plan_code: str = "pro"
    ) -> ProrationResult:
        if period_start.tzinfo is None:
            period_start = period_start.replace(tzinfo=timezone.utc)
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)
        if upgrade_time.tzinfo is None:
            upgrade_time = upgrade_time.replace(tzinfo=timezone.utc)

        total_seconds = max(1, int((period_end - period_start).total_seconds()))
        elapsed_seconds = max(0, min(total_seconds, int((upgrade_time - period_start).total_seconds())))
        remaining_seconds = total_seconds - elapsed_seconds

        # Unused credit from current plan
        unused_credit_cents = (current_price_cents * remaining_seconds) // total_seconds

        # Prorated charge for new plan for remaining period
        prorated_charge_cents = (target_price_cents * remaining_seconds) // total_seconds

        # Net amount due immediately
        net_charge_cents = max(0, prorated_charge_cents - unused_credit_cents)
        dollars = net_charge_cents // 100
        cents = net_charge_cents % 100

        return ProrationResult(
            current_plan_code=current_plan_code,
            target_plan_code=target_plan_code,
            cycle_total_seconds=total_seconds,
            cycle_elapsed_seconds=elapsed_seconds,
            cycle_remaining_seconds=remaining_seconds,
            current_plan_price_cents=current_price_cents,
            target_plan_price_cents=target_price_cents,
            unused_credit_cents=unused_credit_cents,
            prorated_charge_cents=prorated_charge_cents,
            net_charge_cents=net_charge_cents,
            net_charge_usd=f"${dollars}.{cents:02d}"
        )

