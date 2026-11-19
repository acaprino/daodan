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

## Icon sets of the cloud providers (not shipped)

An entry that has `mark_source` instead of `mark` has no file in the repository: the copy of Daodan on the user's machine downloads the owner's package at first use (`service_registry.mark_file`), checks its sha256, reads only the SVG named by `member` and reduces it with `clean_svg`. Daodan does not redistribute these icons. Each owner's terms allow them in architecture diagrams and documentation (the graph is one), and say nothing on redistribution, so they are fetched from the owner, not shipped.

- <https://arch-center.azureedge.net/icons/Azure_Public_Service_Icons_V25.zip>, taken 2026-11-18, sha256 `f293d99252b3638557dd08ccbff9f2529083473d39b373fb2af29a7200351339`, 11 entries. Terms: <https://learn.microsoft.com/en-us/azure/architecture/icons/>. "Microsoft permits the use of these icons in architectural diagrams, training materials, or documentation. You can copy, distribute, and display the icons only for the permitted use unless granted explicit permission by Microsoft. Microsoft reserves all other rights."
- <https://d1.awsstatic.com/onedam/marketing-channels/website/public/shared/architecture-icon-release/Icon-package_07312026.5846e92413caa21490223536cc97f1269e44fa92.zip>, taken 2026-11-18, sha256 `d2d166c453526471749d520e0db022c459abef759d2946cf2dd1d1c992dc6526`, 46 entries. Terms: <https://aws.amazon.com/architecture/icons/>. "We allow customers and partners to use these toolkits and assets to create architecture diagrams." "You can also put icons in materials like whitepapers, presentations, data sheets, and posters."
- <https://services.google.com/fh/files/misc/core-products-icons.zip>, taken 2026-11-18, sha256 `6531a10f58bc599c24d9a455d81dd757c1a03c3c43da9cddf639b859c1c1eece`, 8 entries. Terms: <https://cloud.google.com/icons>. "Here you can find the Google Cloud product icons you need for your diagrams, technical documentation, and more." (no further terms on the page)
- <https://services.google.com/fh/files/misc/google-cloud-legacy-icons.zip>, taken 2026-11-18, sha256 `a6d9d7921758042538b462f03cf64614c2cebd96743b3ed63580a769fc7de3e9`, 19 entries. Terms: <https://cloud.google.com/icons>. "Here you can find the Google Cloud product icons you need for your diagrams, technical documentation, and more." (no further terms on the page)

## Additions

`registry-additions.json` holds the packages and entries the catalogs lack. Those marked `derive` were found on PyPI, crates.io and the Go proxy under the name of an npm package whose repository has the same owner. Those marked `catalog` are curated: `category` says whether an entry is a framework, library, tool or service, and `wrong_signs` take away a sign a catalog gives wrongly. Those marked `model` were proposed by a model and kept only where the packages exist, have one owner and belong to no other entry, and the site answers. Those marked `official` give an entry its mark from the owner (see above).
