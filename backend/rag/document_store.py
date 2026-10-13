import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from backend.config import KB_DIR

logger = logging.getLogger(__name__)


class DocumentChunk:
    def __init__(self, chunk_id: str, source_file: str, title: str, section: str, text: str, metadata: Dict[str, Any]):
        self.chunk_id = chunk_id
        self.source_file = source_file
        self.title = title
        self.section = section
        self.text = text
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_file": self.source_file,
            "title": self.title,
            "section": self.section,
            "text": self.text,
            "metadata": self.metadata,
        }


class DocumentStore:
    def __init__(self, kb_dir: Path = KB_DIR):
        self.kb_dir = kb_dir
        self.chunks: List[DocumentChunk] = []
        self._load_and_chunk()

    def _load_and_chunk(self):
        """Loads and breaks all Cynbit knowledge base JSON documents into indexed semantic chunks."""
        self.chunks = []
        if not self.kb_dir.exists():
            logger.warning(f"Knowledge base directory {self.kb_dir} not found.")
            return

        for json_path in sorted(self.kb_dir.glob("*.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                filename = json_path.name
                if filename == "cynbit_overview.json":
                    self._chunk_overview(data, filename)
                elif filename == "cynbit_services.json":
                    self._chunk_services(data, filename)
                elif filename == "cynbit_products.json":
                    self._chunk_products(data, filename)
                elif filename == "cynbit_bitelevate.json":
                    self._chunk_bitelevate(data, filename)
                elif filename == "cynbit_case_studies.json":
                    self._chunk_case_studies(data, filename)
                elif filename == "cynbit_lifecycle_pricing.json":
                    self._chunk_lifecycle(data, filename)
            except Exception as e:
                logger.error(f"Error loading {json_path}: {e}")

        logger.info(f"Loaded and indexed {len(self.chunks)} semantic chunks from Cynbit Knowledge Base.")

    def _chunk_overview(self, data: Dict[str, Any], filename: str):
        text = f"Cynbit Technologies ({data.get('tagline')}, '{data.get('archetype')}'). Located at {data.get('headquarters')}. {data.get('positioning')} Contact email: {data.get('contacts', {}).get('email')}, Phone: {', '.join(data.get('contacts', {}).get('phone', []))}. Social Mission: {data.get('social_mission')}."
        self.chunks.append(DocumentChunk(
            chunk_id=f"{filename}#overview",
            source_file=filename,
            title="Cynbit Technologies Overview & Positioning",
            section="Company Profile",
            text=text,
            metadata={"domain": "Company", "contacts": data.get("contacts")}
        ))
        
        diff_text = "Cynbit Key Differentiators:\n" + "\n".join(f"- {d}" for d in data.get("differentiators", []))
        self.chunks.append(DocumentChunk(
            chunk_id=f"{filename}#differentiators",
            source_file=filename,
            title="Cynbit Core Architectural Differentiators",
            section="Value Proposition",
            text=diff_text,
            metadata={"domain": "Strategy"}
        ))

    def _chunk_services(self, data: List[Dict[str, Any]], filename: str):
        for srv in data:
            caps = "\n".join(f"- {c}" for c in srv.get("capabilities", []))
            text = (
                f"Service Domain: {srv.get('domain')} - {srv.get('title')}.\n"
                f"Summary: {srv.get('summary')}\n"
                f"Key Capabilities:\n{caps}\n"
                f"Ideal Client Fit: {srv.get('ideal_fit')}\n"
                f"Investment Tier: {srv.get('pricing_tier')}"
            )
            self.chunks.append(DocumentChunk(
                chunk_id=f"{filename}#{srv.get('id')}",
                source_file=filename,
                title=f"Cynbit Service: {srv.get('title')}",
                section=srv.get("domain"),
                text=text,
                metadata={"service_id": srv.get("id"), "domain": srv.get("domain")}
            ))

    def _chunk_products(self, data: List[Dict[str, Any]], filename: str):
        for prod in data:
            features = "\n".join(f"- {f}" for f in prod.get("features", []))
            text = (
                f"Product: {prod.get('name')} ({prod.get('tagline')}).\n"
                f"Description: {prod.get('description')}\n"
                f"Core Features:\n{features}\n"
                f"Target Users: {prod.get('target_users')}"
            )
            self.chunks.append(DocumentChunk(
                chunk_id=f"{filename}#{prod.get('id')}",
                source_file=filename,
                title=f"Cynbit SaaS Product: {prod.get('name')}",
                section="Proprietary SaaS",
                text=text,
                metadata={"product_id": prod.get("id")}
            ))

    def _chunk_bitelevate(self, data: Dict[str, Any], filename: str):
        tracks = "\n".join(f"- {t.get('track')}: {t.get('focus')}" for t in data.get("core_tracks", []))
        text = (
            f"BitElevate Program: {data.get('tagline')}.\n"
            f"Overview: {data.get('overview')}\n"
            f"Certified Architects: {data.get('metrics', {}).get('certified_architects')}\n"
            f"Core Engineering Tracks:\n{tracks}\n"
            f"Diaries: {data.get('student_diaries')}"
        )
        self.chunks.append(DocumentChunk(
            chunk_id=f"{filename}#bitelevate-ecosystem",
            source_file=filename,
            title="BitElevate Architectural Education Ecosystem",
            section="BitElevate",
            text=text,
            metadata={"domain": "Education"}
        ))

    def _chunk_case_studies(self, data: List[Dict[str, Any]], filename: str):
        for cs in data:
            text = (
                f"Case Study: {cs.get('client')} ({cs.get('domain')}).\n"
                f"Key Outcome: {cs.get('outcome_headline')}\n"
                f"Client Challenge: {cs.get('challenge')}\n"
                f"Cynbit Architectural Solution: {cs.get('solution')}\n"
                f"Verified Client Testimonial: \"{cs.get('testimonial')}\""
            )
            self.chunks.append(DocumentChunk(
                chunk_id=f"{filename}#{cs.get('client').lower().replace(' ', '-')}",
                source_file=filename,
                title=f"Case Study: {cs.get('client')} ({cs.get('outcome_headline')})",
                section="Validation & Case Studies",
                text=text,
                metadata={"client": cs.get("client")}
            ))

    def _chunk_lifecycle(self, data: Dict[str, Any], filename: str):
        steps = "\n".join(
            f"Step {s.get('step')} - {s.get('name')} ({s.get('duration')}): {s.get('deliverables')}"
            for s in data.get("architectural_lifecycle", [])
        )
        self.chunks.append(DocumentChunk(
            chunk_id=f"{filename}#lifecycle",
            source_file=filename,
            title="Cynbit 6-Step Architectural Lifecycle",
            section="Process & Methodology",
            text=f"How Cynbit constructs digital success:\n{steps}",
            metadata={"domain": "Engineering Process"}
        ))

        models = "\n".join(
            f"- Model: {m.get('model')} | Investment: {m.get('typical_budget')} | Duration: {m.get('timeline')} | Best for: {m.get('best_for')}"
            for m in data.get("engagement_models", [])
        )
        self.chunks.append(DocumentChunk(
            chunk_id=f"{filename}#engagement-models",
            source_file=filename,
            title="Cynbit Engagement Models & Pricing Guidelines",
            section="Pricing & Architecture",
            text=f"Cynbit Commercial Engagement Models:\n{models}",
            metadata={"domain": "Pricing"}
        ))
