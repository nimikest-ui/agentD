---
name: deep-research
description: "Complete research pipeline with data gathering, processing, analysis, and knowledge storage. Orchestrates tool calling to investigate topics thoroughly and persist findings."
license: MIT
compatibility: designed for agentD
---

# Deep Research Skill

Execute a complete research pipeline: gather raw data → process → analyze → store in memory and knowledge graph.

## Available Tools

You have access to these functions during research:

### Data Gathering
- `browse_url(url)` - Fetch and extract content from a URL
- `search_web(query)` - Search and gather web information
- `scrape_content(url)` - Extract structured data from web pages

### Data Processing
- `process_markdown(raw_data)` - Convert raw content to clean markdown
- `extract_entities(text)` - Identify key entities, dates, relationships
- `structure_findings(data)` - Organize information hierarchically

### Analysis
- `analyze_patterns(data)` - Find patterns and connections in data
- `assess_impact(findings)` - Evaluate significance and implications
- `identify_gaps(research)` - Find missing information

### Knowledge Storage
- `save_to_memory(fact, category)` - Store in persistent memory
- `create_graph_node(name, type, properties)` - Add to knowledge graph
- `link_nodes(from_node, relationship, to_node)` - Create graph connections
- `save_skill_insight(topic, finding)` - Store as reusable skill

## Research Pipeline

### Phase 1: Clarify & Plan
1. Understand what you're researching
2. Break into researchable sub-questions
3. Identify what data sources you'll need

### Phase 2: Gather Data
1. Search and browse multiple authoritative sources
2. Collect both raw data and expert perspectives
3. Document source URLs and credentials

### Phase 3: Process Raw Data
1. Clean and structure the gathered information
2. Extract key entities (people, organizations, dates, technical terms)
3. Identify primary claims and supporting evidence

### Phase 4: Analyze
1. Look for patterns, relationships, contradictions
2. Cross-reference claims across sources
3. Assess confidence levels for each finding
4. Evaluate business/technical impact

### Phase 5: Store Knowledge
1. Save key facts to memory for future use
2. Create graph nodes for major entities
3. Link related concepts together
4. Document gaps for future research

### Phase 6: Synthesize & Report
1. Create comprehensive summary with sources
2. Highlight key insights and implications
3. Document uncertainty and assumptions
4. Suggest next research directions

## Best Practices

- **Multiple sources**: Never rely on one source for complex topics
- **Verify claims**: Cross-reference critical information
- **Document everything**: Track what you found, where, and how confident you are
- **Distinguish fact from opinion**: Be clear about what's verified vs. interpretive
- **Store incrementally**: Save findings as you discover them, not at the end
- **Connect knowledge**: Link related findings in the graph as patterns emerge
- **Be transparent about gaps**: Document what you don't know yet

## Example Flow

User: "Research AI safety concerns in 2024"

1. Plan: Identify sub-questions (regulations, incidents, technical risks, industry response)
2. Gather: Browse regulations, incident reports, research papers, company announcements
3. Process: Extract key events, timelines, affected organizations, technical details
4. Analyze: Find patterns (which countries leading? which companies proactive? what technical approaches?), assess real vs. perceived risk
5. Store: Create nodes for regulators, incidents, organizations, link them together
6. Report: Comprehensive summary with sources, confidence levels, identified gaps

## Common Pitfalls to Avoid

- Stopping research too early - you need multiple perspectives
- Confusing correlation with causation - verify before claiming relationships
- Ignoring contradicting information - document disagreements
- Overgeneralizing from limited data - be specific about scope
- Forgetting to store findings - don't lose insights by not documenting them
