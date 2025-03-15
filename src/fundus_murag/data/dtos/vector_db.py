from pydantic import BaseModel

from fundus_murag.data.dtos.fundus import (
    FundusCollection,
    FundusRecord,
    FundusRecordInternal,
)


class SimilaritySearchResultBase(BaseModel):
    certainty: float
    distance: float


class FundusRecordSemanticSearchResult(SimilaritySearchResultBase):
    record: FundusRecordInternal | FundusRecord


class FundusCollectionSemanticSearchResult(SimilaritySearchResultBase):
    collection: FundusCollection
