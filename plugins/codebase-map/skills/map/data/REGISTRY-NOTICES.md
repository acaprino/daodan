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

The `icon` field names a slug of [Simple Icons](https://simpleicons.org/), released under CC0-1.0. The marks themselves remain the property of their owners; see the project's [disclaimer](https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md) before showing them.

## Additions

`registry-additions.json` holds the packages and entries the catalogs lack. Those marked `derive` were found on PyPI, crates.io and the Go proxy under the name of an npm package whose repository has the same owner.
