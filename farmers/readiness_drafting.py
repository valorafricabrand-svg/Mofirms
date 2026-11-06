from decimal import Decimal

from django.core.exceptions import ValidationError

from .models import BusinessReadinessDraft, FinancialAnalysisRequest


def _money(value):
    return f"{value:,.2f}"


def build_readiness_draft(request):
    if request.request_type != FinancialAnalysisRequest.RequestType.BUSINESS_READINESS:
        raise ValidationError("A readiness draft can only be created for the readiness pilot.")

    citations = []

    def cite(source_id, label, value, source_type="customer_input", formula=""):
        citation = {
            "id": source_id,
            "label": label,
            "value": str(value),
            "source_type": source_type,
        }
        if formula:
            citation["formula"] = formula
        citations.append(citation)
        return f"[{source_id}]"

    business = request.business_name.strip() or request.contact_name.strip()
    cite("business_name", "Business or contact name", business)
    cite("county", "County", request.county)
    activity = request.sector.strip() or "unspecified activity"
    cite("sector", "Business activity", activity)
    cite("business_goal", "Business goal", request.business_goal.strip())
    cite(
        "current_challenge",
        "Main business challenge",
        request.current_challenge.strip(),
    )
    summary = (
        f"{business} is an enterprise with {activity} in {request.county}. "
        f"The stated goal is: {request.business_goal.strip()}. "
        f"The main challenge reported is: {request.current_challenge.strip()}."
    )
    summary_refs = [
        "business_name",
        "county",
        "sector",
        "business_goal",
        "current_challenge",
    ]

    record_labels = {
        "financial_statements": "Financial statements",
        "sales_records": "Sales or income records",
        "expense_records": "Expense or purchase records",
        "cashbook": "Cashbook or bookkeeping records",
        "bank_statements": "Bank statements",
        "business_plan": "Existing business plan",
        "budgets": "Budgets or forecasts",
        "none": "No formal records yet",
    }
    records = [
        record_labels.get(record, record)
        for record in request.records_available
    ]
    cite(
        "records_available",
        "Records reported as available",
        ", ".join(records) if records else "None reported",
    )
    cite(
        "financial_period",
        "Financial period",
        request.financial_period.strip() or "Not provided",
    )
    gaps = []
    next_steps = []
    if not request.records_available or request.records_available == ["none"]:
        gaps.append(
            {
                "text": "No formal financial records were reported.",
                "source_refs": ["records_available"],
            }
        )
        next_steps.append(
            {
                "text": "Before finalising figures, agree which available sales and expense records can support the estimates.",
                "source_refs": ["records_available"],
            }
        )
    if not request.financial_period.strip():
        gaps.append(
            {
                "text": "The period covered by the financial information was not provided.",
                "source_refs": ["financial_period"],
            }
        )
        next_steps.append(
            {
                "text": "Confirm the period covered by the records or estimates.",
                "source_refs": ["financial_period"],
            }
        )
    if not request.seasonality_notes.strip():
        cite(
            "seasonality_notes",
            "Seasonality notes",
            "Not provided",
        )
        gaps.append(
            {
                "text": "Seasonal changes to production, sales, or costs have not been described.",
                "source_refs": ["seasonality_notes"],
            }
        )
        next_steps.append(
            {
                "text": "Confirm which months have materially different production, sales, or costs.",
                "source_refs": ["seasonality_notes"],
            }
        )
    else:
        cite("seasonality_notes", "Seasonality notes", request.seasonality_notes.strip())

    sales = request.average_monthly_sales
    costs = request.average_monthly_costs
    cash_flow = {
        "status": "estimate_not_provided",
        "currency": "KES",
        "period": "monthly",
        "monthly_sales": None,
        "monthly_operating_costs": None,
        "estimated_monthly_difference": None,
        "annualised_sales_arithmetic": None,
        "annualised_costs_arithmetic": None,
        "source_refs": ["average_monthly_sales", "average_monthly_costs"],
        "assumption": (
            "Annualised values multiply the submitted monthly averages by 12. "
            "They are arithmetic illustrations, not forecasts."
        ),
    }
    if sales is None or costs is None:
        cite(
            "average_monthly_sales",
            "Average monthly sales estimate",
            "Not provided",
        )
        cite(
            "average_monthly_costs",
            "Average monthly operating-cost estimate",
            "Not provided",
        )
        gaps.append(
            {
                "text": "A cash-flow difference could not be calculated because paired monthly sales and cost estimates were not provided.",
                "source_refs": ["average_monthly_sales", "average_monthly_costs"],
            }
        )
        next_steps.append(
            {
                "text": "If available, provide sales and operating-cost estimates for the same period; otherwise discuss an appropriate way to build them from records.",
                "source_refs": ["average_monthly_sales", "average_monthly_costs"],
            }
        )
    else:
        difference = sales - costs
        cite("average_monthly_sales", "Average monthly sales estimate", _money(sales))
        cite(
            "average_monthly_costs",
            "Average monthly operating-cost estimate",
            _money(costs),
        )
        cite(
            "estimated_monthly_difference",
            "Arithmetic difference between submitted averages",
            _money(difference),
            source_type="calculation",
            formula="average_monthly_sales - average_monthly_costs",
        )
        annual_sales = sales * Decimal("12")
        annual_costs = costs * Decimal("12")
        cite(
            "annualised_sales_arithmetic",
            "Annualised sales arithmetic",
            _money(annual_sales),
            source_type="calculation",
            formula="average_monthly_sales * 12",
        )
        cite(
            "annualised_costs_arithmetic",
            "Annualised cost arithmetic",
            _money(annual_costs),
            source_type="calculation",
            formula="average_monthly_costs * 12",
        )
        cash_flow.update(
            {
                "status": "illustrative_arithmetic",
                "monthly_sales": _money(sales),
                "monthly_operating_costs": _money(costs),
                "estimated_monthly_difference": _money(difference),
                "annualised_sales_arithmetic": _money(annual_sales),
                "annualised_costs_arithmetic": _money(annual_costs),
                "source_refs": [
                    "average_monthly_sales",
                    "average_monthly_costs",
                    "estimated_monthly_difference",
                    "annualised_sales_arithmetic",
                    "annualised_costs_arithmetic",
                ],
            }
        )
        next_steps.append(
            {
                "text": "Have a reviewer compare these estimates with the stated records and confirm that sales and costs cover the same period.",
                "source_refs": ["average_monthly_sales", "average_monthly_costs", "records_available"],
            }
        )
        revenue_ranges = {
            "under_500k": (Decimal("0"), Decimal("500000")),
            "500k_2m": (Decimal("500000"), Decimal("2000000")),
            "2m_10m": (Decimal("2000000"), Decimal("10000000")),
        }
        annual_band = request.annual_revenue_band
        if annual_band in revenue_ranges:
            low, high = revenue_ranges[annual_band]
            is_outside_band = (
                annual_sales >= high
                if annual_band == "under_500k"
                else annual_sales < low or annual_sales > high
            )
        elif annual_band == "over_10m":
            is_outside_band = annual_sales <= Decimal("10000000")
        else:
            is_outside_band = False
        if is_outside_band:
            cite(
                "annual_revenue_band",
                "Annual revenue range selected",
                request.get_annual_revenue_band_display(),
            )
            gaps.append(
                {
                    "text": "The selected annual revenue range differs from monthly sales multiplied by 12; confirm the period, seasonality, and range.",
                    "source_refs": [
                        "annual_revenue_band",
                        "average_monthly_sales",
                        "annualised_sales_arithmetic",
                    ],
                }
            )
            next_steps.append(
                {
                    "text": "Confirm whether the monthly sales average represents a full year, including seasonal months, and whether the selected annual revenue range is still appropriate.",
                    "source_refs": [
                        "annual_revenue_band",
                        "average_monthly_sales",
                        "seasonality_notes",
                    ],
                }
            )
        if difference < 0:
            gaps.append(
                {
                    "text": "The submitted monthly operating-cost estimate is greater than the submitted monthly sales estimate; confirm both figures and what costs they include.",
                    "source_refs": ["average_monthly_sales", "average_monthly_costs"],
                }
            )
    if records and request.financial_period.strip():
        next_steps.append(
            {
                "text": "Use the records listed for the stated period to review the business summary and cash-flow assumptions.",
                "source_refs": ["records_available", "financial_period"],
            }
        )

    if not gaps:
        gaps.append(
            {
                "text": "No missing-information checks were triggered by the submitted fields; staff still need to validate the information and scope.",
                "source_refs": summary_refs + ["records_available", "financial_period"],
            }
        )
    if not next_steps:
        next_steps.append(
            {
                "text": "A MoFirms reviewer should validate the submitted information and agree the service scope with the customer.",
                "source_refs": summary_refs,
            }
        )

    return {
        "business_summary": summary,
        "cash_flow": cash_flow,
        "key_gaps": gaps,
        "next_steps": next_steps,
        "source_citations": citations,
    }


def build_ai_draft_context(request):
    if request.request_type != FinancialAnalysisRequest.RequestType.BUSINESS_READINESS:
        raise ValidationError("AI draft context is only available for the readiness pilot.")

    rule_draft = build_readiness_draft(request)
    allowed_source_ids = {
        "county",
        "sector",
        "business_goal",
        "current_challenge",
        "average_monthly_sales",
        "average_monthly_costs",
        "records_available",
        "annual_revenue_band",
        "seasonality_notes",
    }
    allowed_source_ids.update(
        citation["id"]
        for citation in rule_draft["source_citations"]
        if citation["source_type"] == "calculation"
    )
    return {
        "task": (
            "Draft a plain-language explanation and practical next steps for staff review. "
            "Do not make lending, investment, insurance, tax, legal, or verification decisions."
        ),
        "source_data": [
            {"id": "county", "value": request.county},
            {"id": "sector", "value": request.sector or "Not provided"},
            {"id": "business_goal", "value": request.business_goal},
            {"id": "current_challenge", "value": request.current_challenge},
            {
                "id": "average_monthly_sales",
                "value": _money(request.average_monthly_sales)
                if request.average_monthly_sales is not None
                else "Not provided",
            },
            {
                "id": "average_monthly_costs",
                "value": _money(request.average_monthly_costs)
                if request.average_monthly_costs is not None
                else "Not provided",
            },
            {
                "id": "records_available",
                "value": request.records_available,
            },
            {
                "id": "annual_revenue_band",
                "value": request.annual_revenue_band or "Not provided",
            },
            {
                "id": "seasonality_notes",
                "value": request.seasonality_notes or "Not provided",
            },
        ],
        "calculated_values": rule_draft["cash_flow"],
        "approved_guidance": [],
        "allowed_source_ids": sorted(allowed_source_ids),
        "requirements": [
            "Return only JSON with business_summary, key_gaps, next_steps, citations.",
            "business_summary must contain text and source_refs.",
            "Every summary, gap, and next-step item must include source_refs.",
            "Use only source ids supplied in source_data, calculated_values, or approved_guidance.",
            "Do not invent figures, facts, policy, or advice.",
            "Do not calculate financial values; use the application-calculated figures if supplied.",
            "Do not claim the customer or evidence is verified.",
        ],
        "personal_data_excluded": [
            "contact_name",
            "phone",
            "email",
            "uploaded_document_contents",
        ],
    }


def validate_ai_draft_output(output, allowed_source_ids):
    if not isinstance(output, dict):
        raise ValidationError("The AI draft must be a JSON object.")
    required_keys = {"business_summary", "key_gaps", "next_steps", "citations"}
    if set(output) != required_keys:
        raise ValidationError("The AI draft has an unexpected response shape.")
    allowed_source_ids = set(allowed_source_ids)
    summary = output["business_summary"]
    if (
        not isinstance(summary, dict)
        or set(summary) != {"text", "source_refs"}
        or not isinstance(summary["text"], str)
        or not summary["text"].strip()
        or len(summary["text"]) > 4000
        or not isinstance(summary["source_refs"], list)
        or not summary["source_refs"]
        or not all(isinstance(source_id, str) for source_id in summary["source_refs"])
    ):
        raise ValidationError("The AI draft summary needs text and source references.")
    if not set(summary["source_refs"]).issubset(allowed_source_ids):
        raise ValidationError("The AI summary uses a source reference that was not provided.")

    if not isinstance(output["citations"], list) or not output["citations"]:
        raise ValidationError("AI citations must be a list.")
    cited_ids = set()
    for citation in output["citations"]:
        if (
            not isinstance(citation, dict)
            or set(citation) != {"source_id", "claim"}
            or not isinstance(citation["source_id"], str)
        ):
            raise ValidationError("Each AI citation must identify a source and claim.")
        if citation["source_id"] not in allowed_source_ids:
            raise ValidationError("The AI draft cites a source that was not provided.")
        if not isinstance(citation["claim"], str) or not citation["claim"].strip():
            raise ValidationError("Each AI citation must describe the supported claim.")
        cited_ids.add(citation["source_id"])
    if not set(summary["source_refs"]).issubset(cited_ids):
        raise ValidationError("Every AI summary source reference must have a matching citation.")

    for field in ("key_gaps", "next_steps"):
        entries = output[field]
        if not isinstance(entries, list) or len(entries) > 10:
            raise ValidationError(f"AI {field.replace('_', ' ')} must be a list of at most 10 items.")
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or set(entry) != {"text", "source_refs"}
                or not isinstance(entry["text"], str)
                or not entry["text"].strip()
                or len(entry["text"]) > 1000
                or not isinstance(entry["source_refs"], list)
                or not entry["source_refs"]
                or not all(isinstance(source_id, str) for source_id in entry["source_refs"])
            ):
                raise ValidationError(
                    f"Each AI {field.replace('_', ' ')} item needs text and source references."
                )
            if not set(entry["source_refs"]).issubset(allowed_source_ids):
                raise ValidationError("The AI draft uses a source reference that was not provided.")
            if not set(entry["source_refs"]).issubset(cited_ids):
                raise ValidationError("Every AI source reference must have a matching citation.")

    return output


def save_readiness_draft(request, user):
    content = build_readiness_draft(request)
    draft, created = BusinessReadinessDraft.objects.get_or_create(
        request=request,
        defaults={
            **content,
            "generation_method": "rules-v1",
            "generated_by": user,
        },
    )
    if not created:
        if draft.review_status == BusinessReadinessDraft.ReviewStatus.APPROVED:
            raise ValidationError(
                "This draft is approved. Create a new request to generate another draft."
            )
        for field, value in content.items():
            setattr(draft, field, value)
        draft.generation_method = "rules-v1"
        draft.generated_by = user
        draft.reviewed_by = None
        draft.reviewed_at = None
        draft.review_notes = ""
        draft.save()
    return draft
