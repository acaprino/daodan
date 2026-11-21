# Registry notices

`service-registry.json` is built by `scripts/registry_build.py` from the sources below, at the versions recorded in the file's `versions` field.

## stack-analyser 1.27.6

The detection rules (names, types, packages, configuration prefixes, files) come from [specfy/stack-analyser](https://github.com/specfy/stack-analyser).

```
The MIT License

Copyright (c) 2023 Specfy (https://www.specfy.io)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

## CNCF Landscape

Names, categories and sites of entries marked `cncf-landscape` come from the [CNCF Landscape](https://github.com/cncf/landscape) (`landscape.yml` at commit `75b47639d132b3a7afa31ecc84a90f61b8072dd6`), © the Cloud Native Computing Foundation and contributors, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: categories are mapped to node types, member and certified-vendor categories are left out, entries are merged by name with the other sources.

## Simple Icons 16.37.0

The files in `marks/` named by an entry whose `from` has `simple-icons` are the SVGs of [Simple Icons](https://simpleicons.org/), released under CC0-1.0, reduced to drawing by `registry_build.py` (`clean_svg`) with the collection's brand colour as `fill`. The marks themselves remain the property of their owners; see the project's [disclaimer](https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md) before showing them.

## Daodan's tiles

Since 18 November 2026 each file in `marks/` is a tile: Daodan's own frame (a white rounded panel, a grey border, a magenta accent) around the mark, which keeps the shape of its source (Simple Icons, or the owner's SVG for an official mark) and the brand colour Simple Icons records. The frame is Daodan's; the mark inside remains the property of its owner, under the terms of its source above and below.

## Official marks

Marks of services that Simple Icons does not have, published by their owner and shipped in `marks/` (named by the entry's `mark`), reduced to drawing by `clean_svg`. `registry-additions.json` keeps the same record (`mark_origin`: URL, terms page, the day the file was taken). The marks remain the property of their owners.

- `checkov`: <https://raw.githubusercontent.com/bridgecrewio/checkov/main/docs/web/images/checkov-logo.svg>, taken 2026-11-18. Terms: <https://github.com/bridgecrewio/checkov/blob/main/LICENSE>. Apache-2.0: the Contributors grant "a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce, prepare Derivative Works of, publicly display, publicly perform, sublicense, and distribute the Work"; section 6 grants no trademark rights "except as required for reasonable and customary use in describing the origin of the Work".
- `dokku`: <https://raw.githubusercontent.com/dokku/dokku/master/docs/assets/dokku-logo.svg>, taken 2026-11-18. Terms: <https://github.com/dokku/dokku/blob/master/LICENSE>. MIT licence of the repository, which holds the file (docs/assets): the right "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies"; no trademark statement found.
- `expodev`: <https://raw.githubusercontent.com/expo/logos/main/svg/logo-type-a.svg>, taken 2026-11-18. Terms: <https://expo.dev/brand>. "Use a permitted Expo logo to inform others that your project integrates with Expo."
- `pinecone`: <https://www.pinecone.io/images/brand/pinecone-logomark-black.svg>, taken 2026-11-18. Terms: <https://www.pinecone.io/brand/>. "You may: Use the Pinecone name and logo to refer to Pinecone and its products accurately. Show that your product uses, integrates with, or is built on Pinecone."
- `supabase.auth`: <https://supabase.com/brand-assets/supabase-icon-green-transparent.svg>, taken 2026-11-18. Terms: <https://supabase.com/brand-assets>. "Use the Supabase logos only to refer to Supabase. Do not change the files or the logo colors." The file is the owner's, reduced to drawing by `clean_svg` with the shapes and colours as published.
- `supabase.functions`: <https://supabase.com/brand-assets/supabase-icon-green-transparent.svg>, taken 2026-11-18. Terms: <https://supabase.com/brand-assets>. "Use the Supabase logos only to refer to Supabase. Do not change the files or the logo colors." The file is the owner's, reduced to drawing by `clean_svg` with the shapes and colours as published.
- `supabase.postgres`: <https://supabase.com/brand-assets/supabase-icon-green-transparent.svg>, taken 2026-11-18. Terms: <https://supabase.com/brand-assets>. "Use the Supabase logos only to refer to Supabase. Do not change the files or the logo colors." The file is the owner's, reduced to drawing by `clean_svg` with the shapes and colours as published.
- `supabase.realtime`: <https://supabase.com/brand-assets/supabase-icon-green-transparent.svg>, taken 2026-11-18. Terms: <https://supabase.com/brand-assets>. "Use the Supabase logos only to refer to Supabase. Do not change the files or the logo colors." The file is the owner's, reduced to drawing by `clean_svg` with the shapes and colours as published.
- `supabase.storage`: <https://supabase.com/brand-assets/supabase-icon-green-transparent.svg>, taken 2026-11-18. Terms: <https://supabase.com/brand-assets>. "Use the Supabase logos only to refer to Supabase. Do not change the files or the logo colors." The file is the owner's, reduced to drawing by `clean_svg` with the shapes and colours as published.
- `twentycrm`: <https://raw.githubusercontent.com/twentyhq/twenty/main/packages/twenty-website/public/images/core/logo.svg>, taken 2026-11-18. Terms: <https://twenty.com/terms>. "Please do not use the Twenty name or logo in a way that suggests endorsement or affiliation without our permission; using them to truthfully refer to the open-source project is fine." The same section grants no rights in the trademarks.

## Daodan's pictograms of the cloud services

The marks of the services of AWS, Azure and Google Cloud (an entry of `registry-additions.json` whose `by` is `daodan`) are drawings of Daodan's, made on 18 November 2026: a pictogram drawn from nothing on Daodan's tile, in the colours the provider's own icon of that service has. No path of a provider's icon is in them, and none is the provider's icon or its logo; the names of the services remain their owners'. They take the place of the providers' icon packages, which Daodan fetched at first use until that day and never shipped: those packages' terms speak of diagrams and documentation, not of redistribution.

- AWS, 47: `aws.amplifyhosting`, `aws.apigateway`, `aws.athena`, `aws.bedrock`, `aws.cloudfront`, `aws.cloudsearch`, `aws.cloudwatch`, `aws.codebuild`, `aws.codepipeline`, `aws.cognito`, `aws.comprehend`, `aws.documentdb`, `aws.dynamodb`, `aws.ebs`, `aws.ec2`, `aws.ecr`, `aws.ecs`, `aws.efs`, `aws.eks`, `aws.elasticache`, `aws.fargate`, `aws.glacier`, `aws.glue`, `aws.kafka`, `aws.kinesis`, `aws.kms`, `aws.lambda`, `aws.lightsail`, `aws.memorydb`, `aws.mq`, `aws.neptune`, `aws.opensearch`, `aws.polly`, `aws.rds`, `aws.redshift`, `aws.rekognition`, `aws.s3`, `aws.sagemaker`, `aws.secretsmanager`, `aws.ses`, `aws.sfn`, `aws.sns`, `aws.sqs`, `aws`, `aws.timestream`, `aws.transcribe`, `aws.translate`.
- Azure, 14: `azure.aks`, `azure.ci`, `azure.cosmosdb`, `azure.functions`, `azure.maps`, `azure.mariadb`, `azure.mysql`, `azure.openai`, `azure.postgres`, `azure.redis`, `azure.sql`, `azure.staticwebapps`, `azure.storage`, `azure`.
- Google Cloud, 29: `gcp.aiplatform`, `gcp.appengine`, `gcp.artifactregistry`, `gcp.bigquery`, `gcp.bigtable`, `gcp.cloudbuild`, `gcp.cloudrun`, `gcp.dataflow`, `gcp.dataproc`, `gcp.datastore`, `gcp.dialogflow`, `gcp.dns`, `gcp.functions`, `gcp.gce`, `gcp.gcs`, `gcp.gke`, `gcp.kms`, `gcp.language`, `gcp.logging`, `gcp.memorystore`, `gcp.pubsub`, `gcp.secretmanager`, `gcp.spanner`, `gcp.speech`, `gcp.sql`, `gcp`, `gcp.tasks`, `gcp.vertex`, `gcp.vision`.

## Additions

`registry-additions.json` holds the packages and entries the catalogs lack. Those marked `derive` were found on PyPI, crates.io and the Go proxy under the name of an npm package whose repository has the same owner. Records marked `corpus` add package identifiers verified against project manifests. The [project-model benchmark](../../benchmarks/project-model/README.md) documents the corpus and how to reproduce the comparison. Those marked `catalog` are curated: `category` says whether an entry is a framework, library, tool or service, and `wrong_signs` take away a sign a catalog gives wrongly. Those marked `model` were proposed by a model and kept only where the packages exist, have one owner and belong to no other entry, and the site answers. Those marked `official` give an entry its mark from the owner (see above). The `category` of 245 `project` entries that had signs and none (from `actixweb` to `zod`) was proposed by a model on 19 November 2026; the machine checks only that it is one of the four.
