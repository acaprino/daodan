# input-validation-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:input-validation-auditor`; content basis.
- Authored control family: SD011-020. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD012.

Defect: The name x' OR 1=1 -- changes the predicate and exposes both rows instead of matching a literal name. Source-to-SQL interpretation is required for full credit, not just string concatenation.

Correct / must_not_report: Parameterized binding prevents the demonstrated injection. Do not require stripping apostrophes, a separate schema library, ORM or a global denylist.

## normalized_value (scorer only)

Controls: SD011.

Requirement: The consumed label must contain no less-than sign. Request text is percent-encoded; validator rejects literal < but permits encoded %3C. Validation must constrain the decoded sink value.

Defect: Encoded %3C passes the pre-decode check and becomes forbidden < at the sensitive sink; the consumed value was not validated.

Correct / must_not_report: The exact sink value is checked after decoding; accepted labels need no second validation.

## query_object (scorer only)

Controls: SD013.

Requirement: NoSQL selector must match the caller name literally. Driver interprets dictionary values beginning with $ as operators. Request name may be any JSON value; valid names are strings.

Defect: A caller supplies {"$ne":null}; the driver interprets it as an operator rather than a name, broadening matches.

Correct / must_not_report: Strings are literal driver values, so rejecting operator dictionaries is sufficient without a SQL-style escape.

## interpreter_boundaries (scorer only)

Controls: SD014-018.

Requirement: Adapters execute shell source, LDAP filter source, template source or serialized object construction exactly as named. Safe adapters treat fixed-program arguments, escaped LDAP text, fixed template data and JSON data as inert. Do not execute these adapters during qualification.

Defect: Each unsafe adapter receives attacker-controlled source/object input. Scorer requires distinct shell/LDAP/template/deserialization interpretation paths; claiming only SQL does not cover these.

Correct / must_not_report: Safe adapter contracts explicitly separate structure from data, and JSON constructs no arbitrary objects. No execution of dangerous payloads is permitted.

## expanded_work (scorer only)

Controls: SD019-020.

Requirement: Regex work must be bounded by at most 256 input characters, and expanded archive work by at most 4096 bytes. risky_match may backtrack exponentially above the admitted input size; expand_bounded(limit) enforces its expanded-byte limit incrementally.

Defect: Regex can receive arbitrarily large attacker input and compressed size does not bound expansion. Distinct required findings: unbounded matching and expanded-byte admission.

Correct / must_not_report: Effective presink character and incremental expansion bounds meet the stated limits; no requirement for a particular regex library.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.
