from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation_knowledge import KNOWLEDGE_CHUNKS


@dataclass(slots=True)
class RecommendationContext:
    start_date: str
    end_date: str
    metrics: dict[str, float]
    previous_metrics: dict[str, float]
    top_products: list[dict]
    risk_products: list[dict]


class RecommendationGenerator:
    def generate(self, context: RecommendationContext) -> dict:
        raise NotImplementedError


class RulesBasedRecommendationGenerator(RecommendationGenerator):
    def generate(self, context: RecommendationContext) -> dict:
        metrics = context.metrics
        previous_metrics = context.previous_metrics
        insights: list[dict] = []

        revenue_growth = _pct_change(metrics["revenue"], previous_metrics["revenue"])
        profit_growth = _pct_change(metrics["net_profit"], previous_metrics["net_profit"])

        if metrics["profit_margin"] < 12:
            insights.append(
                {
                    "title": "Margin pressure needs attention",
                    "body": (
                        f"Profit margin is {metrics['profit_margin']:.1f}% for this period. "
                        "Review COGS, refunds, and ad efficiency before pushing more spend."
                    ),
                    "severity": "warning",
                    "metric_keys": ["profit_margin", "net_profit", "cogs"],
                }
            )

        if metrics["tacos"] > 15:
            insights.append(
                {
                    "title": "Advertising is taking a large share of revenue",
                    "body": (
                        f"TACOS is {metrics['tacos']:.1f}%, which means a meaningful share of "
                        "total sales is being reinvested into ads. Validate whether hero SKUs "
                        "are still producing acceptable contribution margin."
                    ),
                    "severity": "warning",
                    "metric_keys": ["tacos", "ad_spend", "revenue"],
                }
            )

        if metrics["refund_rate"] > 4:
            insights.append(
                {
                    "title": "Refund drag is elevated",
                    "body": (
                        f"Refund rate is {metrics['refund_rate']:.1f}%. Check listing accuracy, "
                        "customer feedback, and fulfillment issues on the most refunded SKUs."
                    ),
                    "severity": "warning",
                    "metric_keys": ["refund_rate", "refunds", "revenue"],
                }
            )

        if revenue_growth is not None and profit_growth is not None and revenue_growth > 0 and profit_growth < revenue_growth:
            insights.append(
                {
                    "title": "Revenue is growing faster than profit",
                    "body": (
                        f"Revenue changed {revenue_growth:.1f}% versus the previous period, but "
                        f"net profit changed {profit_growth:.1f}%. Growth is coming with cost pressure."
                    ),
                    "severity": "neutral",
                    "metric_keys": ["revenue", "net_profit", "fees", "ad_spend"],
                }
            )

        if context.top_products:
            hero_sku = context.top_products[0]
            insights.append(
                {
                    "title": f"{hero_sku['sku']} is your profit leader",
                    "body": (
                        f"{hero_sku['sku']} contributed {hero_sku['net_profit']:.0f} in net profit "
                        f"at a {hero_sku['profit_margin']:.1f}% margin. Protect inventory and ad efficiency on this SKU."
                    ),
                    "severity": "positive",
                    "metric_keys": ["net_profit", "profit_margin"],
                }
            )

        if metrics["roas"] >= 3:
            insights.append(
                {
                    "title": "Ad efficiency is supporting growth",
                    "body": (
                        f"ROAS is {metrics['roas']:.2f}x across the selected period. "
                        "Keep watching TACOS to make sure overall profit quality stays strong as spend scales."
                    ),
                    "severity": "positive",
                    "metric_keys": ["roas", "tacos", "ad_spend"],
                }
            )

        if metrics["avg_order_value"] > 0:
            aov_change = _pct_change(metrics["avg_order_value"], previous_metrics["avg_order_value"])
            change_text = (
                f"AOV changed {aov_change:.1f}% versus the previous period."
                if aov_change is not None
                else "There is no previous-period AOV yet for comparison."
            )
            insights.append(
                {
                    "title": "Average order value is worth monitoring",
                    "body": (
                        f"AOV is {metrics['avg_order_value']:.2f}. {change_text} "
                        "This is useful when deciding whether pricing, bundles, or cross-sell tactics are improving basket quality."
                    ),
                    "severity": "neutral",
                    "metric_keys": ["avg_order_value", "orders_count", "revenue"],
                }
            )

        if context.risk_products:
            risk_sku = context.risk_products[0]
            insights.append(
                {
                    "title": f"{risk_sku['sku']} needs a profitability review",
                    "body": (
                        f"{risk_sku['sku']} is at {risk_sku['profit_margin']:.1f}% margin with "
                        f"{risk_sku['net_profit']:.0f} net profit. Review pricing, ad bid levels, and COGS."
                    ),
                    "severity": "warning",
                    "metric_keys": ["profit_margin", "net_profit", "acos"],
                }
            )

        if len(insights) < 3:
            insights.append(
                {
                    "title": "Catalog diversification can reduce concentration risk",
                    "body": (
                        "Keep comparing top and bottom SKUs by profit margin so growth does not become too dependent "
                        "on a single hero SKU or on heavily discounted long-tail products."
                    ),
                    "severity": "neutral",
                    "metric_keys": ["net_profit", "profit_margin"],
                }
            )

        insights = insights[:4]

        llm_prompt_template = (
            "You are an Amazon seller profitability analyst. Use the supplied KPI metrics, period-over-period "
            "changes, top products, risk products, and metric knowledge chunks to generate 3 prioritized "
            "recommendations. Focus on concrete actions tied to profit, ad efficiency, refunds, and SKU mix."
        )

        summary = (
            f"Analyzed {context.start_date} to {context.end_date}. Revenue={metrics['revenue']:.2f}, "
            f"NetProfit={metrics['net_profit']:.2f}, ProfitMargin={metrics['profit_margin']:.2f}%, "
            f"TACOS={metrics['tacos']:.2f}%, ACOS={metrics['acos']:.2f}%, RefundRate={metrics['refund_rate']:.2f}%."
        )

        return {
            "summary": summary,
            "insights": insights,
            "llm_prompt_template": llm_prompt_template,
            "knowledge_chunks": KNOWLEDGE_CHUNKS,
        }


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / abs(previous)) * 100, 2)
