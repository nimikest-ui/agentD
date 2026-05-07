---
name: deep-research
description: "Structured research pipeline that gathers data into a session directory, processes it, analyzes for patterns, then extracts into memory, knowledge graph, and reusable skills."
license: MIT
compatibility: designed for agentD
---

# Deep Research Skill

Execute the complete research pipeline. Data flows from raw gathering → processing → analysis → knowledge extraction.

## Research Directory Structure

Create research session: `~/.agentd/research/{research-name}/`
```
research-name/
├── raw_data/          (gathered from browse_url, search_web, scrape_content)
├── processed/         (cleaned via process_markdown, extract_entities, structure_findings)
├── analysis.json      (patterns via analyze_patterns, assess_impact, identify_gaps)
├── findings.md        (synthesis of all discoveries)
└── metadata.json      (what becomes memory/skills)
```

## Tool Functions Available

### Phase 1: Data Gathering
Use these to collect information:
- `browse_url(url)` → raw content file in `raw_data/`
- `search_web(query)` → search results in `raw_data/`
- `scrape_content(url)` → extracted page in `raw_data/`

### Phase 2: Data Processing
Clean and structure the raw data:
- `process_markdown(raw_data)` → convert to clean markdown
- `extract_entities(text)` → identify entities, save to `processed/`
- `structure_findings(data)` → organize hierarchically, save to `processed/`

### Phase 3: Analysis
Find patterns and significance:
- `analyze_patterns(data)` → connections and clusters, save to `analysis.json`
- `assess_impact(findings)` → evaluate significance and implications
- `identify_gaps(research)` → find missing information

### Phase 4: Knowledge Extraction
Transform into reusable knowledge:
- `save_to_memory(fact, category)` → persistent memory
- `create_graph_node(name, type, properties)` → knowledge graph
- `link_nodes(from_node, relationship, to_node)` → create relationships
- `save_skill_insight(topic, finding)` → new skill file in `.deepagents/skills/`

## Execution Pipeline

1. **Initialize**: Create research directory with name and metadata
2. **Gather**: Use browse_url, search_web, scrape_content → populate raw_data/
3. **Process**: Use process_markdown, extract_entities, structure_findings → populate processed/
4. **Analyze**: Use analyze_patterns, assess_impact, identify_gaps → write analysis.json
5. **Extract**: Parse analysis and:
   - Call save_to_memory() for key facts
   - Call create_graph_node() for entities
   - Call link_nodes() for relationships
   - Call save_skill_insight() for discovered methodologies → creates new skill
6. **Report**: Generate findings.md with all discoveries and next steps

## Key Principle

All data stays in one research directory. Analysis happens on the complete dataset. Discoveries are then distributed to:
- **Memory** (facts you'll use)
- **Graph** (how things relate)
- **Skills** (processes you discovered)

## Example

User: "Research AI safety in 2024"

1. Create: `~/.agentd/research/ai-safety-2024/`
2. Gather: browse regulations, incidents, papers → `raw_data/`
3. Process: extract orgs, dates, claims → `processed/`
4. Analyze: find patterns (which orgs active? which countries leading?) → `analysis.json`
5. Extract:
   - Memory: "AI safety regulations increased 2024"
   - Graph nodes: Organization "DeepMind", Category "Safety Research"
   - Links: DeepMind -publishes→ Safety Papers
   - Skill: New skill "ai-safety-analysis" with methodology discovered
6. Report: findings.md with sources, confidence, gaps

## Best Practices

- **One directory per research** - Keeps all data together
- **Process incrementally** - Don't wait until end to save findings
- **Extract all knowledge types** - Facts, relationships, and processes
- **Create skills from discoveries** - Turn "how to X" findings into reusable skills
- **Document gaps** - Identify what still needs research for next iteration
