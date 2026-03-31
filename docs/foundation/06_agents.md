# 6. Claude Agent Design

Use role-based prompt modules, not one giant prompt.

## Research Agent
- **Purpose:** gather and synthesize sources, produce research dossier
- **Inputs:** topic, module, source pack
- **Outputs:** normalized topic research JSON, bibliographic list, claim table

## Historian Agent
- **Purpose:** verify historical order, detect anachronisms, separate original vs modern forms
- **Outputs:** corrected timeline, historical caution notes, priority/discovery warnings

## Story Architect Agent
- **Purpose:** design the episode arc, assign one learning goal per episode, propose everyday analogies
- **Outputs:** episode blueprint, analogy map, narrative progression

## Scriptwriter Agent
- **Purpose:** write the content in house style
- **Outputs:** X version, short video version, long-form version, article version

## Citation Auditor Agent
- **Purpose:** verify support for non-obvious claims, ensure proper referencing
- **Outputs:** missing citation report, weak-claim warnings, final reference list

## Repurposing Agent
- **Purpose:** adapt one core script into all platforms
- **Outputs:** platform-specific text assets, title variations, captions, CTAs, hashtag suggestions

## Compliance Agent
- **Purpose:** check policy alignment, flag low-value mass-content patterns, set disclosure requirements
- **Outputs:** pass/fail, disclosure flags, publication notes
