"""
AnalyticsAgent — Dani, Analytics Manager.
Specialises in data analysis, KPIs, performance dashboards, and ROI analysis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent


class AnalyticsAgent(BaseAgent):
    """
    Dani — Analytics Manager.

    Extended capabilities:
    - KPI framework definition
    - Data interpretation and storytelling
    - Dashboard design recommendations
    - Attribution model analysis
    - ROI calculations
    """

    def define_kpi_framework(
        self,
        business_type: str,
        objectives: List[str],
        channels: List[str],
    ) -> str:
        """Define a comprehensive KPI framework."""
        objectives_str = ", ".join(objectives)
        channels_str = ", ".join(channels)
        prompt = (
            f"Define a KPI framework.\n\n"
            f"Business type: {business_type}\n"
            f"Business objectives: {objectives_str}\n"
            f"Active channels: {channels_str}\n\n"
            "Produce:\n"
            "1. North Star Metric\n"
            "2. Primary KPIs (5-7) with targets and measurement method\n"
            "3. Secondary/diagnostic metrics per channel\n"
            "4. Vanity metrics to avoid\n"
            "5. Reporting cadence recommendations\n"
            "6. Dashboard layout suggestion"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "kpi_framework", "business": business_type},
        )

    def analyse_performance_data(
        self,
        channel: str,
        metrics: Dict[str, Any],
        period: str = "last 30 days",
    ) -> str:
        """Analyse performance data and provide insights."""
        metrics_text = "\n".join(f"  {k}: {v}" for k, v in metrics.items())
        prompt = (
            f"Analyse {channel} performance data for {period}.\n\n"
            f"Metrics:\n{metrics_text}\n\n"
            "Provide:\n"
            "1. Executive summary (3 sentences)\n"
            "2. Key wins\n"
            "3. Problem areas with root cause analysis\n"
            "4. Statistical anomalies to investigate\n"
            "5. 5 actionable recommendations\n"
            "6. Forecast for next period (optimistic/realistic/pessimistic)"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "performance_analysis", "channel": channel, "period": period},
        )

    def calculate_roi(
        self,
        campaign_name: str,
        investment: float,
        revenue_attributed: float,
        costs: Optional[Dict[str, float]] = None,
    ) -> str:
        """Calculate and analyse campaign ROI."""
        costs_text = ""
        if costs:
            costs_text = "\nAdditional costs:\n" + "\n".join(
                f"  {k}: ${v}" for k, v in costs.items()
            )
        prompt = (
            f"Calculate and analyse ROI for: {campaign_name}\n\n"
            f"Investment: ${investment}\n"
            f"Revenue attributed: ${revenue_attributed}"
            f"{costs_text}\n\n"
            "Calculate: ROI %, ROAS, Net profit, Break-even point.\n"
            "Provide: performance verdict, comparison to industry benchmarks, "
            "and 3 recommendations to improve ROI in the next campaign."
        )
        return self.execute_task(
            prompt,
            metadata={
                "type": "roi_calculation",
                "campaign": campaign_name,
                "investment": investment,
                "revenue": revenue_attributed,
            },
        )

    def build_attribution_report(
        self,
        touchpoints: List[Dict[str, Any]],
        conversion_value: float,
    ) -> str:
        """Build a multi-touch attribution analysis."""
        touchpoints_text = "\n".join(
            f"  {i+1}. {tp.get('channel', 'unknown')} - {tp.get('action', 'interaction')} "
            f"(Day {tp.get('day', '?')})"
            for i, tp in enumerate(touchpoints)
        )
        prompt = (
            f"Build a multi-touch attribution analysis.\n\n"
            f"Customer journey touchpoints:\n{touchpoints_text}\n\n"
            f"Conversion value: ${conversion_value}\n\n"
            "Apply and compare: First-touch, Last-touch, Linear, "
            "Time-decay, and Position-based (U-shaped) attribution models.\n"
            "Recommend the best model for this business with justification."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "attribution_report", "conversion_value": conversion_value},
        )

    def create_dashboard_spec(
        self, stakeholder: str, report_frequency: str, channels: List[str]
    ) -> str:
        """Design a performance dashboard specification."""
        channels_str = ", ".join(channels)
        prompt = (
            f"Design a performance dashboard for: {stakeholder}\n\n"
            f"Report frequency: {report_frequency}\n"
            f"Channels to cover: {channels_str}\n\n"
            "Specify:\n"
            "1. Dashboard sections and layout\n"
            "2. Charts/visualisations for each section\n"
            "3. Key metrics per visualisation\n"
            "4. Data sources and refresh rate\n"
            "5. Automated alert thresholds\n"
            "6. Tool recommendation (Looker Studio, Tableau, etc.)"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "dashboard_spec", "stakeholder": stakeholder},
        )
