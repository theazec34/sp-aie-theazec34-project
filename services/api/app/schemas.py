from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category: str
    count: int
    percentage: float


class StatusBreakdown(BaseModel):
    status: str
    count: int
    percentage: float


class ScoreDistribution(BaseModel):
    score: int
    count: int


class InvalidBreakdown(BaseModel):
    missing_location_id: int
    invalid_category: int
    empty_description: int
    closed_no_score: int
    missing_reporter_id: int
    score_out_of_range: int


class SatisfactionIndex(BaseModel):
    scored_cases: int
    total_closed: int
    average: float
    distribution: list[ScoreDistribution]


class AnalysisReport(BaseModel):
    source_file: str
    total_records: int
    valid_records: int
    invalid_records: int
    invalid_breakdown: InvalidBreakdown
    by_category: list[CategoryBreakdown]
    by_status: list[StatusBreakdown]
    satisfaction: SatisfactionIndex
