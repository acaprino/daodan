import type { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  schema: "schema.graphql",
  generates: { "src/generated/graphql.ts": { plugins: ["typescript"] } },
};

export default config;
