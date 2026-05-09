# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## 5. Design-Driven Development

**Design doc is the source of truth. Explain before you change. Plan before you build.**

### 5.1 Design Doc Synchronization (MANDATORY)

When you change the system design — architecture, agent responsibilities, communication protocols, data models, SKILL workflows, or interruption mechanisms — you **MUST** update the design document at `docs/superpowers/specs/2026-05-03-ai-job-copilot-design.md` in the same commit.

This is **not optional**. Violations include:
- Adding/removing an agent without updating the agent list
- Changing a SKILL workflow without updating the SKILL section
- Modifying A2A protocol behavior without updating the protocol section
- Altering data model fields without updating the data model section
- Changing the interrupt/replay mechanism without updating the Supervisor section

**Rule:** If your code change makes a future reader of the design doc misunderstand how the system works, the doc must be updated. No exceptions.

### 5.2 Pre-Modification Explanation (MANDATORY)

Before making **any change to existing code**, you MUST:
1. Explain what you are about to change and why
2. Identify the affected files and the specific functions/classes/sections
3. State the expected behavioral difference after the change

This applies to all modifications — even single-line fixes. If the change is trivial (typo, format) the explanation can be one sentence. For non-trivial changes, the explanation must be substantial enough that the user can evaluate whether the change is correct before seeing the code.

**You MUST NOT write any code before the user acknowledges the explanation.** Do not edit files, do not write new files — explain first, wait for confirmation, then implement.

### 5.3 Pre-Development Design Proposal (MANDATORY)

Before implementing **new features or incomplete/planned features** (e.g., anything from Phase 5/6 of the design doc that is not yet done), you MUST:
1. Produce a concrete design or modification plan
2. Include: what files will be created/modified, the approach (architecture, algorithms, data flow), and rationale for key decisions
3. Surface tradeoffs and alternatives where applicable

**You MUST NOT start coding until the user reviews and approves the proposal.** Once approved, implement exactly what the proposal describes — no extras, no scope creep.

---

**Answer in Chinese.**