# Entry routing: business

These lines are the entry workflows and knowledge of the `business` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- business plan, pricing, go-to-market, piano aziendale: `business:saas-business-plan`
- contract, NDA, terms of service, contratto: `business:legal-advisor` (agent to dispatch)
- privacy policy, GDPR, DPA, informativa privacy: `business:privacy-doc-generator` (agent to dispatch)
