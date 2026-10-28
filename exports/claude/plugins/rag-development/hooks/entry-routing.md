# Entry routing: rag-development

These lines are the entry workflows and knowledge of the `rag-development` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- `/rag-development:rag-audit`: TRIGGER WHEN: the user asks to review, audit, or validate a RAG pipeline: chunking, embeddings, retrieval, reranking, or production readiness.
