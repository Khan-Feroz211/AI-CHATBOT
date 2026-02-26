#!/usr/bin/env python3
"""
Simple WhatsApp Cloud API pricing estimator.
Defaults to Pakistan 2026 reference rates (PKR) for conversation/message windows.
"""

from dataclasses import dataclass

# Reference rates (adjust when Meta updates pricing)
# Values are per conversation/message depending on Meta category rules.
PAKISTAN_RATES_PKR = {
    "marketing": 0.882,       # PKR per conversation
    "utility": 0.160,         # PKR per conversation
    "authentication": 0.129,  # PKR per conversation
    "service": 0.0,           # Customer-initiated service window (often zero-rated)
}


@dataclass
class Estimate:
    marketing: int = 0
    utility: int = 0
    authentication: int = 0
    service: int = 0

    def monthly_cost_pkr(self, rates=PAKISTAN_RATES_PKR) -> float:
        total = (
            self.marketing * rates["marketing"]
            + self.utility * rates["utility"]
            + self.authentication * rates["authentication"]
            + self.service * rates["service"]
        )
        return round(total, 2)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="WhatsApp pricing estimator (Pakistan rates).")
    parser.add_argument("--marketing", type=int, default=0, help="Marketing conversations per month")
    parser.add_argument("--utility", type=int, default=0, help="Utility conversations per month")
    parser.add_argument("--authentication", type=int, default=0, help="Authentication conversations per month")
    parser.add_argument("--service", type=int, default=0, help="Customer-initiated service conversations per month")

    args = parser.parse_args()
    est = Estimate(
        marketing=args.marketing,
        utility=args.utility,
        authentication=args.authentication,
        service=args.service,
    )
    total = est.monthly_cost_pkr()

    print("=== WhatsApp Cloud API Cost Estimate (Pakistan, PKR) ===")
    print(f"Marketing:       {args.marketing}  @ PKR {PAKISTAN_RATES_PKR['marketing']} each")
    print(f"Utility:         {args.utility}    @ PKR {PAKISTAN_RATES_PKR['utility']} each")
    print(f"Authentication:  {args.authentication}  @ PKR {PAKISTAN_RATES_PKR['authentication']} each")
    print(f"Service:         {args.service}    @ PKR {PAKISTAN_RATES_PKR['service']} each")
    print("---------------------------------------------")
    print(f"Estimated monthly total: PKR {total}")


if __name__ == "__main__":
    main()
