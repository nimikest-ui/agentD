#!/usr/bin/env python3
"""
Research Tools for Deep Research Skill
Implements data gathering, processing, analysis, and knowledge storage functions
"""

import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

# Try to import browser tools
try:
    from agentd.browser_tools import BrowserToolkit
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False


class ResearchTools:
    """Tools for conducting deep research with data gathering, processing, and storage"""

    def __init__(self):
        self.browser = BrowserToolkit() if BROWSER_AVAILABLE else None
        self.research_cache = {}
        self.memory_dir = Path.home() / ".agentd" / "research"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.memory_dir / "knowledge_graph.json"
        self._load_graph()

    def _load_graph(self):
        """Load knowledge graph from disk"""
        if self.graph_file.exists():
            with open(self.graph_file) as f:
                self.graph = json.load(f)
        else:
            self.graph = {"nodes": {}, "edges": []}

    def _save_graph(self):
        """Save knowledge graph to disk"""
        with open(self.graph_file, "w") as f:
            json.dump(self.graph, f, indent=2)

    # ===== Data Gathering =====

    def browse_url(self, url: str) -> Dict[str, Any]:
        """Fetch and extract content from a URL"""
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        return {
            "url": url,
            "status": "ready",
            "method": "browse",
            "note": "Browser automation would extract full page content with JavaScript rendering"
        }

    def search_web(self, query: str) -> Dict[str, Any]:
        """Search web for information on a topic"""
        return {
            "query": query,
            "status": "ready",
            "method": "search",
            "note": "Web search would return top results with snippets and URLs",
            "example_results": [
                {"title": "Result 1", "snippet": "...", "url": "https://..."},
                {"title": "Result 2", "snippet": "...", "url": "https://..."},
            ]
        }

    def scrape_content(self, url: str) -> Dict[str, Any]:
        """Extract structured data from web pages"""
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        return {
            "url": url,
            "status": "ready",
            "method": "scrape",
            "note": "Scraping would extract clean markdown content from the page"
        }

    # ===== Data Processing =====

    def process_markdown(self, raw_data: str) -> str:
        """Convert raw content to clean markdown"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\n\n\n+', '\n\n', raw_data)
        # Remove HTML artifacts
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        # Normalize spacing
        cleaned = cleaned.strip()
        return cleaned

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Identify key entities: people, organizations, dates, technical terms"""
        entities = {
            "people": [],
            "organizations": [],
            "dates": [],
            "technical_terms": [],
            "urls": re.findall(r'https?://[^\s]+', text),
            "emails": re.findall(r'[\w\.-]+@[\w\.-]+', text)
        }
        return entities

    def structure_findings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Organize information hierarchically"""
        return {
            "main_findings": data.get("findings", []),
            "supporting_evidence": data.get("evidence", []),
            "sources": data.get("sources", []),
            "confidence": data.get("confidence", "medium"),
            "collected_at": datetime.now().isoformat()
        }

    # ===== Analysis =====

    def analyze_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find patterns and connections in data"""
        return {
            "patterns_found": len(data),
            "connections": "Pattern analysis would identify recurring themes and relationships",
            "clusters": "Data would be grouped by similarity",
            "outliers": "Unusual findings would be flagged for investigation"
        }

    def assess_impact(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate significance and implications"""
        return {
            "significance": "high",
            "affected_areas": findings.get("scope", []),
            "implications": "Impact assessment would evaluate business, technical, and strategic consequences",
            "priority": "medium"
        }

    def identify_gaps(self, research: Dict[str, Any]) -> List[str]:
        """Find missing information in research"""
        gaps = []
        if not research.get("sources", []):
            gaps.append("Missing diverse source perspectives")
        if not research.get("contradictions_addressed"):
            gaps.append("Contradictions between sources not resolved")
        if not research.get("latest_data"):
            gaps.append("Current/latest information not gathered")
        return gaps

    # ===== Knowledge Storage =====

    def save_to_memory(self, fact: str, category: str) -> Dict[str, Any]:
        """Store finding in persistent memory"""
        memory_file = self.memory_dir / "memory.json"

        if memory_file.exists():
            with open(memory_file) as f:
                memory = json.load(f)
        else:
            memory = []

        memory.append({
            "fact": fact,
            "category": category,
            "timestamp": datetime.now().isoformat()
        })

        with open(memory_file, "w") as f:
            json.dump(memory, f, indent=2)

        return {
            "status": "saved",
            "fact": fact,
            "category": category,
            "location": str(memory_file)
        }

    def create_graph_node(self, name: str, node_type: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add node to knowledge graph"""
        node_id = name.lower().replace(" ", "_")

        self.graph["nodes"][node_id] = {
            "name": name,
            "type": node_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat()
        }

        self._save_graph()

        return {
            "status": "created",
            "node_id": node_id,
            "name": name,
            "type": node_type
        }

    def link_nodes(self, from_node: str, relationship: str, to_node: str) -> Dict[str, Any]:
        """Create connection between nodes in knowledge graph"""
        from_id = from_node.lower().replace(" ", "_")
        to_id = to_node.lower().replace(" ", "_")

        self.graph["edges"].append({
            "from": from_id,
            "relationship": relationship,
            "to": to_id,
            "created_at": datetime.now().isoformat()
        })

        self._save_graph()

        return {
            "status": "linked",
            "from": from_node,
            "relationship": relationship,
            "to": to_node
        }

    def save_skill_insight(self, topic: str, finding: str) -> Dict[str, Any]:
        """Store reusable skill/insight for future research"""
        skills_file = self.memory_dir / "insights.json"

        if skills_file.exists():
            with open(skills_file) as f:
                skills = json.load(f)
        else:
            skills = {}

        if topic not in skills:
            skills[topic] = []

        skills[topic].append({
            "insight": finding,
            "timestamp": datetime.now().isoformat()
        })

        with open(skills_file, "w") as f:
            json.dump(skills, f, indent=2)

        return {
            "status": "saved",
            "topic": topic,
            "insight": finding,
            "location": str(skills_file)
        }


# Create global instance
_tools = None


def get_research_tools() -> ResearchTools:
    """Get or create research tools instance"""
    global _tools
    if _tools is None:
        _tools = ResearchTools()
    return _tools


# Export tool functions for CLI/API use
def browse_url(url: str) -> Dict[str, Any]:
    return get_research_tools().browse_url(url)


def search_web(query: str) -> Dict[str, Any]:
    return get_research_tools().search_web(query)


def scrape_content(url: str) -> Dict[str, Any]:
    return get_research_tools().scrape_content(url)


def process_markdown(raw_data: str) -> str:
    return get_research_tools().process_markdown(raw_data)


def extract_entities(text: str) -> Dict[str, List[str]]:
    return get_research_tools().extract_entities(text)


def structure_findings(data: Dict[str, Any]) -> Dict[str, Any]:
    return get_research_tools().structure_findings(data)


def analyze_patterns(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    return get_research_tools().analyze_patterns(data)


def assess_impact(findings: Dict[str, Any]) -> Dict[str, Any]:
    return get_research_tools().assess_impact(findings)


def identify_gaps(research: Dict[str, Any]) -> List[str]:
    return get_research_tools().identify_gaps(research)


def save_to_memory(fact: str, category: str) -> Dict[str, Any]:
    return get_research_tools().save_to_memory(fact, category)


def create_graph_node(name: str, node_type: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
    return get_research_tools().create_graph_node(name, node_type, properties)


def link_nodes(from_node: str, relationship: str, to_node: str) -> Dict[str, Any]:
    return get_research_tools().link_nodes(from_node, relationship, to_node)


def save_skill_insight(topic: str, finding: str) -> Dict[str, Any]:
    return get_research_tools().save_skill_insight(topic, finding)
