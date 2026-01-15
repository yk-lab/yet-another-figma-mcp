# Changelog

## [0.2.0](https://github.com/yk-lab/yet-another-figma-mcp/compare/v0.1.3...v0.2.0) (2026-01-15)


### Features

* add i18n support for CLI messages ([#71](https://github.com/yk-lab/yet-another-figma-mcp/issues/71)) ([0fcb76c](https://github.com/yk-lab/yet-another-figma-mcp/commit/0fcb76c138986ed75fc02d13fe685e9dd74b519a))
* **dx:** add devcontainer configuration ([#78](https://github.com/yk-lab/yet-another-figma-mcp/issues/78)) ([3cff06c](https://github.com/yk-lab/yet-another-figma-mcp/commit/3cff06c40a60e79abbbfe62f15f303bc1599f76a)), closes [#26](https://github.com/yk-lab/yet-another-figma-mcp/issues/26)
* **dx:** add qlty maintainability badge and configure bandit ([#77](https://github.com/yk-lab/yet-another-figma-mcp/issues/77)) ([e860910](https://github.com/yk-lab/yet-another-figma-mcp/commit/e8609108e9f8b36cc838c1b694205747c0ac9e1e)), closes [#19](https://github.com/yk-lab/yet-another-figma-mcp/issues/19)
* **dx:** add Taskfile for common development commands ([#75](https://github.com/yk-lab/yet-another-figma-mcp/issues/75)) ([fdabd0c](https://github.com/yk-lab/yet-another-figma-mcp/commit/fdabd0ca1edd1a42f64b0afc9514bc13a0cedbfb))
* **dx:** add VSCode settings for better developer experience ([#74](https://github.com/yk-lab/yet-another-figma-mcp/issues/74)) ([4a59fb0](https://github.com/yk-lab/yet-another-figma-mcp/commit/4a59fb0cec527d2a006942f26bd357a50eab6ae4)), closes [#30](https://github.com/yk-lab/yet-another-figma-mcp/issues/30)
* **figma:** add custom User-Agent header to FigmaClient ([#73](https://github.com/yk-lab/yet-another-figma-mcp/issues/73)) ([95ebb98](https://github.com/yk-lab/yet-another-figma-mcp/commit/95ebb9800a925f0af3b2ac352a1df4d3c23df95e)), closes [#41](https://github.com/yk-lab/yet-another-figma-mcp/issues/41)
* **tools:** add depth and simplified parameters for AI-optimized node responses ([#83](https://github.com/yk-lab/yet-another-figma-mcp/issues/83)) ([6a93e25](https://github.com/yk-lab/yet-another-figma-mcp/commit/6a93e25dcdb99c9dabb61fa3395be242031ffca2))


### Bug Fixes

* **ci:** correct pytest-randomly seed option in flaky test workflow ([#76](https://github.com/yk-lab/yet-another-figma-mcp/issues/76)) ([93a5a95](https://github.com/yk-lab/yet-another-figma-mcp/commit/93a5a950dc0ee42ff27bf805e633f67c3610146e)), closes [#62](https://github.com/yk-lab/yet-another-figma-mcp/issues/62)
* URLのハイフン形式node_idをコロン形式に正規化 ([#82](https://github.com/yk-lab/yet-another-figma-mcp/issues/82)) ([15382c8](https://github.com/yk-lab/yet-another-figma-mcp/commit/15382c8f081050418c456a63d19ba08a9f77251b))

## [0.1.3](https://github.com/yk-lab/yet-another-figma-mcp/compare/v0.1.2...v0.1.3) (2025-12-02)


### Bug Fixes

* improve MCP tool definitions for better LLM compatibility ([#69](https://github.com/yk-lab/yet-another-figma-mcp/issues/69)) ([fa451b8](https://github.com/yk-lab/yet-another-figma-mcp/commit/fa451b891c3b5cd866cba8e7c8e4221931ff3115))

## [0.1.2](https://github.com/yk-lab/yet-another-figma-mcp/compare/v0.1.1...v0.1.2) (2025-12-01)


### Bug Fixes

* integrate PyPI publish into release-please workflow ([#63](https://github.com/yk-lab/yet-another-figma-mcp/issues/63)) ([f5d546d](https://github.com/yk-lab/yet-another-figma-mcp/commit/f5d546dc55913ca66048f206c19800f9bd180c0a))

## [0.1.1](https://github.com/yk-lab/yet-another-figma-mcp/compare/v0.1.0...v0.1.1) (2025-11-30)


### Bug Fixes

* add error handling to MCP server call_tool to prevent crashes ([#59](https://github.com/yk-lab/yet-another-figma-mcp/issues/59)) ([f090b58](https://github.com/yk-lab/yet-another-figma-mcp/commit/f090b588728e8c05720fd194225217449529c7d6))

## 0.1.0 (2025-11-30)


### Features

* add integration tests for cache flow and MCP server ([#48](https://github.com/yk-lab/yet-another-figma-mcp/issues/48)) ([5098024](https://github.com/yk-lab/yet-another-figma-mcp/commit/50980244c0f7662697f07eda482d9a05e8b33d46))
* **cli:** implement cache command for Figma file caching ([#40](https://github.com/yk-lab/yet-another-figma-mcp/issues/40)) ([91435ca](https://github.com/yk-lab/yet-another-figma-mcp/commit/91435ca51556c2623b1f32b8d6afe155cbbedb30))
* **figma:** complete Figma API client with error handling and retry ([#36](https://github.com/yk-lab/yet-another-figma-mcp/issues/36)) ([0a61b8a](https://github.com/yk-lab/yet-another-figma-mcp/commit/0a61b8a8772e5e542f09e5a232e1decb969cae2b))
* GitHub Actions CI/CD とカバレッジ計測の設定 ([#45](https://github.com/yk-lab/yet-another-figma-mcp/issues/45)) ([1c76252](https://github.com/yk-lab/yet-another-figma-mcp/commit/1c76252d037c409b997fbd2839614e58253260f3))
* implement serve command for MCP server ([#43](https://github.com/yk-lab/yet-another-figma-mcp/issues/43)) ([a40287b](https://github.com/yk-lab/yet-another-figma-mcp/commit/a40287b4d9e969262b0b3caf56599bbfbbc08f9b))
* implement status command and refactor CLI to package structure ([#47](https://github.com/yk-lab/yet-another-figma-mcp/issues/47)) ([6fe5349](https://github.com/yk-lab/yet-another-figma-mcp/commit/6fe534903a86d43ccc7a845aa4ae60ecef7fb6aa))
* improve MCP tools error handling and add case-insensitive search ([#46](https://github.com/yk-lab/yet-another-figma-mcp/issues/46)) ([8f03be7](https://github.com/yk-lab/yet-another-figma-mcp/commit/8f03be73951a56a9f6c9e86f5bad56ce77cc8327))
* initial project setup with MCP server skeleton ([#31](https://github.com/yk-lab/yet-another-figma-mcp/issues/31)) ([e669a87](https://github.com/yk-lab/yet-another-figma-mcp/commit/e669a87fc214f54cf92a02b09556dd3e9f185f44))
* 進捗表示とキャッシュタイムスタンプ記録の追加 ([#44](https://github.com/yk-lab/yet-another-figma-mcp/issues/44)) ([9f697e0](https://github.com/yk-lab/yet-another-figma-mcp/commit/9f697e01f293f8dd714b376316505fe05ee3bbcb))


### Documentation

* add badges to README ([#34](https://github.com/yk-lab/yet-another-figma-mcp/issues/34)) ([9ffa8e9](https://github.com/yk-lab/yet-another-figma-mcp/commit/9ffa8e99fb956fabe1f0254310f335ac8d858f0f))
* add environment variables, cache directory, and CLI commands to CLAUDE.md ([#49](https://github.com/yk-lab/yet-another-figma-mcp/issues/49)) ([8914a4d](https://github.com/yk-lab/yet-another-figma-mcp/commit/8914a4df58e6ae07ff8ebc563eac5627ed960d04)), closes [#33](https://github.com/yk-lab/yet-another-figma-mcp/issues/33)
* add Figma API token setup guide ([#51](https://github.com/yk-lab/yet-another-figma-mcp/issues/51)) ([c8d298c](https://github.com/yk-lab/yet-another-figma-mcp/commit/c8d298c38a4279f6eb8d4c6d162b0fa466a6da12)), closes [#17](https://github.com/yk-lab/yet-another-figma-mcp/issues/17)
* add MCP Inspector guide for debugging and testing ([#50](https://github.com/yk-lab/yet-another-figma-mcp/issues/50)) ([0be6ff4](https://github.com/yk-lab/yet-another-figma-mcp/commit/0be6ff4791c4afcd567e7da850f5ca16ff03b646)), closes [#25](https://github.com/yk-lab/yet-another-figma-mcp/issues/25)
* improve CLAUDE.md with architecture focus and specific commands ([#32](https://github.com/yk-lab/yet-another-figma-mcp/issues/32)) ([9843ab5](https://github.com/yk-lab/yet-another-figma-mcp/commit/9843ab58755868686db2bc2961ca73b4689bb603))
