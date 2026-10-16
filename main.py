import math

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Commission model", layout="wide")


def gross_where_target_is_reached(
    base_salary: float,
    target_compensation: float,
    initial_rate: float,
    minimum_gross_sales: float,
) -> float:
    """Gross sales at which pay reaches the target.

    Commission is zero through the minimum. Only gross above that floor earns
    the initial rate. Returns infinity when a positive gap cannot be closed
    because the initial rate is zero.
    """
    gap = max(target_compensation - base_salary, 0.0)
    if gap == 0:
        return minimum_gross_sales
    if initial_rate <= 0:
        return math.inf
    return minimum_gross_sales + gap / (initial_rate / 100.0)


def pay_at(
    gross: float,
    base_salary: float,
    target_compensation: float,
    initial_rate: float,
    post_target_rate: float,
    minimum_gross_sales: float,
    gross_at_target: float,
) -> dict[str, float | str]:
    """Split commission into the unpaid floor, the initial tier, and the post-target tier.

    Gross through the minimum earns nothing. Gross above the minimum earns the
    initial rate until target compensation is reached, then the post-target
    rate. Effective rate is total commission divided by gross.
    """
    gap = max(target_compensation - base_salary, 0.0)
    if gross <= minimum_gross_sales:
        initial_commission = 0.0
        post_commission = 0.0
        tier = "Below minimum"
        marginal_rate = 0.0
    elif (not math.isfinite(gross_at_target)) or gross <= gross_at_target:
        initial_commission = (gross - minimum_gross_sales) * initial_rate / 100.0
        post_commission = 0.0
        tier = "Initial rate"
        marginal_rate = initial_rate
    else:
        initial_commission = gap
        post_commission = (gross - gross_at_target) * post_target_rate / 100.0
        tier = "Post-target"
        marginal_rate = post_target_rate

    commission = initial_commission + post_commission
    if gross > 0:
        effective_rate = commission / gross * 100.0
    else:
        effective_rate = marginal_rate

    return {
        "gross": gross,
        "total_compensation": base_salary + commission,
        "commission": commission,
        "initial_commission": initial_commission,
        "post_commission": post_commission,
        "effective_rate": effective_rate,
        "tier": tier,
    }


def axis_max(gross_sales: float, gross_at_target: float) -> float:
    """Span the selected gross and, when it is nearby, the rate change."""
    selected = max(gross_sales, 0.0)
    if math.isfinite(gross_at_target) and gross_at_target > 0:
        if selected == 0 or gross_at_target <= selected * 8:
            return max(selected * 1.15, gross_at_target * 1.6, 1.0)
    return max(selected * 1.25, 1.0)


def sample_gross(ceiling: float, required: list[float]) -> list[float]:
    count = 301
    values = [ceiling * i / (count - 1) for i in range(count)]
    for gross in required:
        if 0 <= gross <= ceiling:
            values.append(gross)
    return sorted(set(values))


def money(amount: float) -> str:
    """Format dollars for Streamlit markdown, which treats $ as LaTeX."""
    return f"\\${amount:,.0f}"


def build_chart(
    curve: pd.DataFrame,
    selected: pd.DataFrame,
    ceiling: float,
    gross_at_target: float,
    target_compensation: float,
    minimum_gross_sales: float,
) -> alt.LayerChart:
    """Dual-axis chart: gross on x, compensation on the left, effective rate on the right."""
    series_scale = alt.Scale(
        domain=["Total compensation", "Effective commission rate"],
        range=["#4C78A8", "#E45756"],
    )
    x_encoding = alt.X(
        "gross:Q",
        title="Gross sales ($)",
        scale=alt.Scale(domain=[0, ceiling], nice=False, zero=True),
        axis=alt.Axis(format="$,.3s"),
    )
    tooltips = [
        alt.Tooltip("gross:Q", title="Gross sales", format="$,.0f"),
        alt.Tooltip("total_compensation:Q", title="Total compensation", format="$,.0f"),
        alt.Tooltip("commission:Q", title="Commission", format="$,.0f"),
        alt.Tooltip("effective_rate:Q", title="Effective commission rate", format=".2f"),
        alt.Tooltip("tier:N", title="Tier"),
    ]
    legend = alt.Legend(title=None, orient="top", direction="horizontal")

    compensation = (
        alt.Chart(curve)
        .transform_filter(alt.datum.series == "Total compensation")
        .mark_line(strokeWidth=2.5)
        .encode(
            x=x_encoding,
            y=alt.Y(
                "total_compensation:Q",
                title="Total compensation ($)",
                scale=alt.Scale(zero=True, domain=[0, 200000]),
                axis=alt.Axis(format="$,.3s", titleColor="#4C78A8"),
            ),
            color=alt.Color("series:N", scale=series_scale, legend=legend),
            tooltip=tooltips,
        )
    )
    rate = (
        alt.Chart(curve)
        .transform_filter(alt.datum.series == "Effective commission rate")
        .mark_line(strokeWidth=2.5, strokeDash=[7, 4])
        .encode(
            x=x_encoding,
            y=alt.Y(
                "effective_rate:Q",
                title="Effective commission rate (%)",
                scale=alt.Scale(zero=True, domain=[0, 5]),
                axis=alt.Axis(format=".2f", orient="right", titleColor="#E45756"),
            ),
            color=alt.Color("series:N", scale=series_scale, legend=legend),
            tooltip=tooltips,
        )
    )
    layers: list[alt.Chart] = []
    if 0 < minimum_gross_sales <= ceiling:
        minimum_guide = pd.DataFrame(
            {
                "gross": [minimum_gross_sales],
                "label": ["Minimum gross"],
            }
        )
        layers.append(
            alt.Chart(minimum_guide)
            .mark_rule(strokeDash=[2, 3], color="#C4C4C4")
            .encode(
                x="gross:Q",
                tooltip=[
                    alt.Tooltip("label:N", title="Guide"),
                    alt.Tooltip("gross:Q", title="Gross sales", format="$,.0f"),
                ],
            )
        )
    if math.isfinite(gross_at_target) and 0 < gross_at_target <= ceiling and not (
        math.isclose(gross_at_target, minimum_gross_sales, abs_tol=1)
    ):
        target_gross = pd.DataFrame(
            {
                "gross": [gross_at_target],
                "total_compensation": [target_compensation],
                "label": ["Target reached"],
            }
        )
        layers.append(
            alt.Chart(target_gross)
            .mark_rule(strokeDash=[5, 4], color="#9A9A9A")
            .encode(
                x="gross:Q",
                tooltip=[
                    alt.Tooltip("label:N", title="Guide"),
                    alt.Tooltip("gross:Q", title="Gross sales", format="$,.0f"),
                    alt.Tooltip(
                        "total_compensation:Q",
                        title="Total compensation",
                        format="$,.0f",
                    ),
                ],
            )
        )

    selected_gross = float(selected["gross"].iloc[0])
    target_on_chart = math.isfinite(gross_at_target) and 0 < gross_at_target <= ceiling
    if 0 < selected_gross <= ceiling and not (
        target_on_chart and math.isclose(selected_gross, gross_at_target, abs_tol=1)
    ):
        selected_guide = pd.DataFrame(
            {
                "gross": [selected_gross],
                "label": ["Selected gross"],
            }
        )
        layers.append(
            alt.Chart(selected_guide)
            .mark_rule(color="green", strokeWidth=2)
            .encode(
                x="gross:Q",
                tooltip=[
                    alt.Tooltip("label:N", title="Guide"),
                    alt.Tooltip("gross:Q", title="Gross sales", format="$,.0f"),
                ],
            )
        )

    layers.extend([compensation, rate])
    return (
        alt.layer(*layers)
        .resolve_scale(y="independent")
        .properties(
            height=460,
            title="Total compensation and effective commission rate by gross sales",
        )
    )


st.title("Commission model")
st.caption(
    "Commission is 0% through the minimum gross. Gross above that earns the initial rate "
    "until target compensation is reached, then the post-target rate."
)

with st.sidebar:
    st.title("Configuration")
    base_salary = st.number_input(
        "Base salary",
        min_value=0,
        max_value=1_000_000,
        value=104_000,
        step=1_000,
        help="Paid at every level of gross sales.",
    )
    target_compensation = st.number_input(
        "Target compensation",
        min_value=0,
        max_value=1_000_000,
        value=150_000,
        step=1_000,
        help="Total pay at which the commission rate changes.",
    )
    gross_sales = st.number_input(
        "Gross sales",
        min_value=0,
        max_value=20_000_000,
        value=1_500_000,
        step=100_000,
        help="Scenario marked on the chart. The lines sweep across gross sales around it.",
    )
    minimum_gross_sales = st.number_input(
        "Minimum gross sales",
        min_value=0,
        max_value=1_000_000,
        value=330_000,
        step=10_000,
        help="Gross sales earn no commission until this amount. The rate applies only above it.",
    )
    commission_rate = st.slider(
        "Commission rate (%)",
        min_value=0.0,
        max_value=5.0,
        value=1.5,
        step=0.1,
        help="Percent of gross above the minimum until target compensation is reached.",
    )
    post_target_rate = st.slider(
        "Post-target commission (%)",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.1,
        help="Percent of gross paid after target compensation is reached.",
    )

base_salary = float(base_salary)
target_compensation = float(target_compensation)
gross_sales = float(gross_sales)
commission_rate = float(commission_rate)
post_target_rate = float(post_target_rate)
minimum_gross_sales = float(minimum_gross_sales)
gross_at_target = gross_where_target_is_reached(
    base_salary, target_compensation, commission_rate, minimum_gross_sales
)
ceiling = 5000000  # axis_max(gross_sales, gross_at_target)
selected_pay = pay_at(
    gross_sales,
    base_salary,
    target_compensation,
    commission_rate,
    post_target_rate,
    minimum_gross_sales,
    gross_at_target,
)

curve = pd.DataFrame(
    [
        pay_at(
            gross,
            base_salary,
            target_compensation,
            commission_rate,
            post_target_rate,
            minimum_gross_sales,
            gross_at_target,
        )
        for gross in sample_gross(
            ceiling, [gross_sales, gross_at_target, minimum_gross_sales]
        )
    ]
)
compensation_curve = curve.assign(series="Total compensation")
rate_curve = curve.assign(series="Effective commission rate")
chart_curve = pd.concat([compensation_curve, rate_curve], ignore_index=True)
selected = pd.DataFrame(
    [
        {**selected_pay, "series": "Total compensation"},
        {**selected_pay, "series": "Effective commission rate"},
    ]
)

total = float(selected_pay["total_compensation"])
commission = float(selected_pay["commission"])
effective_rate = float(selected_pay["effective_rate"])
initial_commission = float(selected_pay["initial_commission"])
post_commission = float(selected_pay["post_commission"])

metric_total, metric_commission, metric_rate, metric_tier = st.columns(4)
metric_total.metric("Total compensation", f"${total:,.0f}")
metric_commission.metric("Commission", f"${commission:,.0f}")
metric_rate.metric("Effective commission rate", f"{effective_rate:.2f}%")
metric_tier.metric("Tier at this gross", str(selected_pay["tier"]))

if math.isfinite(gross_at_target):
    st.caption(
        f"Target compensation is reached at {money(gross_at_target)} of gross sales. "
        f"At the selected gross, {money(initial_commission)} of commission is on gross above the minimum "
        f"and {money(post_commission)} is at the post-target rate."
    )
else:
    st.caption(
        "The initial commission rate does not close the gap between base salary and target compensation, "
        "so the post-target rate never applies. "
        f"At the selected gross, commission is {money(commission)}."
    )

if math.isfinite(gross_at_target) and gross_at_target > ceiling:
    st.caption(
        f"The rate change is at {money(gross_at_target)} of gross, beyond this chart. "
        "Raise gross sales or the initial rate to bring it into view."
    )

st.caption(
    "Bottom axis: gross sales. Left axis, solid line: total compensation. "
    "Right axis, dashed line: effective commission rate, which is commission divided by gross. "
    "The pale guide is the minimum gross. The gray guide is where pay reaches the target. "
    "The green guide is the selected gross."
)

st.altair_chart(
    build_chart(
        chart_curve,
        selected,
        ceiling,
        gross_at_target,
        target_compensation,
        minimum_gross_sales,
    ),
    width="stretch",
)
