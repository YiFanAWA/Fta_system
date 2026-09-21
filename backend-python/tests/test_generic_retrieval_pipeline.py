import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from common_fault_schema import FaultEntity  # noqa: E402
from domain_adapter_contract import ExactFieldMatches, RetrievalFieldValues  # noqa: E402
from generic_retrieval_pipeline import (  # noqa: E402
    GenericFaultRetrievalPipeline,
    GenericRerankerDocumentBuilder,
    ParentEntityLoader,
)


class _Adapter:
    def parse_source(self, payload):  # pragma: no cover - protocol fixture
        raise NotImplementedError

    def normalize_entity(self, entity):  # pragma: no cover - protocol fixture
        return entity

    def build_retrieval_chunks(self, entities):  # pragma: no cover - protocol fixture
        return ()

    def extract_exact_fields(self, question):
        return ExactFieldMatches(
            fault_codes=("B00002",) if "B00002" in question else (),
            parameters=("P2",) if "P2" in question else (),
        )

    def retrieval_field_values(self, entity):
        return RetrievalFieldValues(
            semantic_primary=entity.description,
            semantic_cause=" ".join(entity.causes),
            semantic_auxiliary="auxiliary " + entity.fault_code,
            exact_identifier=entity.fault_code,
            exact_parameters=entity.parameters,
            metadata={"domain_marker": "fixture"},
            reranker_fields=(
                ("Identifier", (entity.fault_code,)),
                ("Primary", (entity.description,)),
                ("Cause", entity.causes),
            ),
        )


def _entity(code, description, causes=(), parameters=()):
    return FaultEntity(
        entity_id=f"test:fixture:s1:{code}",
        domain="test",
        manufacturer="Fixture",
        system="S1",
        fault_code=code,
        description=description,
        causes=tuple(causes),
        parameters=tuple(parameters),
    )


class GenericRetrievalPipelineTests(unittest.TestCase):
    def test_parent_loader_is_keyed_by_entity_id(self):
        entity = _entity("B00001", "alpha")
        loader = ParentEntityLoader.from_entities([entity])
        self.assertIs(loader.load(entity.entity_id), entity)
        with self.assertRaises(KeyError):
            loader.load("missing")

    def test_document_builder_keeps_parent_identity_and_role_fields(self):
        entity = _entity("B00001", "alpha", ("cause alpha",))
        values = _Adapter().retrieval_field_values(entity)
        document = GenericRerankerDocumentBuilder().build(entity, values)
        self.assertEqual(entity.entity_id, document.entity_id)
        self.assertEqual(entity.entity_id, document.metadata["entity_id"])
        self.assertIn("Identifier: B00001", document.text)
        self.assertIn("Cause: cause alpha", document.text)

    def test_exact_identifier_is_pinned_and_parameter_signal_is_logged(self):
        entities = [
            _entity("B00001", "alpha", ("cause alpha",), ("P1",)),
            _entity("B00002", "beta", ("cause beta",), ("P2",)),
        ]

        def encode(texts):
            vectors = []
            for text in texts:
                value = str(text).lower()
                vectors.append([1.0, 0.0] if "alpha" in value else [0.0, 1.0])
            return np.asarray(vectors, dtype=float)

        pipeline = GenericFaultRetrievalPipeline(_Adapter(), entities, encode)
        result = pipeline.retrieve("B00002 P2")
        self.assertEqual(entities[1].entity_id, result.guarded_rank[0])
        self.assertEqual(entities[1].entity_id, result.rrf_rank[0])
        self.assertEqual(("P2",), result.matched_parameters_by_entity[entities[1].entity_id])
        self.assertIn(entities[1].entity_id, result.candidate_pool)


if __name__ == "__main__":
    unittest.main()
