# Questions

Record a question with `ask` (`id`, `phase`, `text`), then ask it with the
host's question tool or list it and close the turn. First line: one decision,
as a question. Then the facts it needs, anchored and repeated. Two to four
options with their consequence, the recommended first with its reason. Cut
words, never constraints, risks, irreversible effects or costs.

Record the reply with `answer` (`question`, `text`, `source` `question-tool`,
`chat` or `continue`, and `withdraw` when the user drops what it served):
only the user's own words, settling only what they state.
