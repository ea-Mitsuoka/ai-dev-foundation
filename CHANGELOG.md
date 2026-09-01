# Changelog

## [2.1.1](https://github.com/ea-Mitsuoka/ai-dev-foundation/compare/v2.1.0...v2.1.1) (2026-09-01)


### Bug Fixes

* **ci:** keep contents permission on jobs that read the repository ([#19](https://github.com/ea-Mitsuoka/ai-dev-foundation/issues/19)) ([9e62a23](https://github.com/ea-Mitsuoka/ai-dev-foundation/commit/9e62a23b4e7ffed6415f3d287b71e6295615f035))

## [2.1.0](https://github.com/ea-Mitsuoka/ai-dev-foundation/compare/v2.0.0...v2.1.0) (2026-09-01)


### Features

* **guardrails:** bind untrusted content as data on every task route ([c47e67e](https://github.com/ea-Mitsuoka/ai-dev-foundation/commit/c47e67e37362493709b5d31af333fb3ec9b556ca))
* **guardrails:** bind untrusted content as data on every task route ([48672e4](https://github.com/ea-Mitsuoka/ai-dev-foundation/commit/48672e4d12546f67b9eea25a96bca0b1bb41b5e8)), closes [#6](https://github.com/ea-Mitsuoka/ai-dev-foundation/issues/6)


### Bug Fixes

* **inheritance:** close out the ADR-0019 identity repoint ([#13](https://github.com/ea-Mitsuoka/ai-dev-foundation/issues/13)) ([b7678f3](https://github.com/ea-Mitsuoka/ai-dev-foundation/commit/b7678f366465f81738709cf094bb952bae66f4f2))

## [2.0.0](https://github.com/ea-Mitsuoka/ai-dev-foundation/compare/v1.10.0...v2.0.0) (2026-08-31)


### ⚠ BREAKING CHANGES

* **inheritance:** new children bootstrapped from the ADR-0015 export now record ea-Mitsuoka/ai-dev-foundation as their direct parent.

### Miscellaneous Chores

* **inheritance:** repoint fleet identity to the ea-Mitsuoka account ([aa27d18](https://github.com/ea-Mitsuoka/ai-dev-foundation/commit/aa27d18d60979e7a6859d1e7af789e2809d559b9)), closes [#1](https://github.com/ea-Mitsuoka/ai-dev-foundation/issues/1)

## [1.10.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.9.2...v1.10.0) (2026-08-30)


### Features

* **inheritance:** add private source authentication ([#204](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/204)) ([1ff40c4](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/1ff40c4ccb4073790c1cc2eed5ea9d4197d6465c))

## [1.9.2](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.9.1...v1.9.2) (2026-08-29)


### Bug Fixes

* **ci:** skip plan-limited jobs in private repos ([#202](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/202)) ([610ec97](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/610ec97b7cc7966184c5e0e1350b38db5c14498f))

## [1.9.1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.9.0...v1.9.1) (2026-08-28)


### Bug Fixes

* **doctor:** support descendant suite selection ([#199](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/199)) ([4cf3225](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/4cf3225360a54d17f98b404eaa257f735ea4f860))

## [1.9.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.8.4...v1.9.0) (2026-08-28)


### Features

* **ai:** add inherited presentation skill ([#196](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/196)) ([7f6609f](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/7f6609f5be3de61b98a1902141adbd43c160f187))

## [1.8.4](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.8.3...v1.8.4) (2026-08-14)


### Bug Fixes

* **dependencies:** remove invalid empty Dependabot config ([#188](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/188)) ([784f175](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/784f175060c05759bbc7ee60998d435d26125b0e)), closes [#187](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/187)

## [1.8.3](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.8.2...v1.8.3) (2026-08-09)


### Bug Fixes

* **inheritance:** harden synchronization preflight ([#182](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/182)) ([51678bf](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/51678bf53017466f6ee202611ee6937cc1539193))

## [1.8.2](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.8.1...v1.8.2) (2026-08-09)


### Bug Fixes

* **ci:** upgrade CodeQL Action to v4 ([#176](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/176)) ([98cd5ed](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/98cd5ed7b4c53728ca1ab34dfb79ca6efb0fd8e7))

## [1.8.1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.8.0...v1.8.1) (2026-08-08)


### Bug Fixes

* **inheritance:** allow GitHub workflow expressions ([#171](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/171)) ([c518f1a](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/c518f1a4c73b85e4319a38a86bc78d35aef7604d)), closes [#159](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/159)
* **inheritance:** protect bootstrapped project docs ([#174](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/174)) ([b658e39](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/b658e39a192bee47e8264974ea048f3ffbe4edc9)), closes [#173](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/173)

## [1.8.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.7.0...v1.8.0) (2026-08-08)


### Features

* **inheritance:** apply confirmed child bootstrap ([#170](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/170)) ([a678c5a](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/a678c5ad91a5af68d08a4543a843f8a4bbd37d2f)), closes [#159](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/159)
* **inheritance:** plan direct-child bootstrap ([#168](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/168)) ([ecf50e4](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/ecf50e49dae5d9fc03c857e1f46167558bab0e22))

## [1.7.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.6.0...v1.7.0) (2026-08-08)


### Features

* **inheritance:** classify propagation impact ([#167](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/167)) ([82ba5bb](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/82ba5bb1125db69522e261eb69d90b60bdac651d))
* **inheritance:** model fleet lifecycle states ([#166](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/166)) ([bc2d61c](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/bc2d61c7cfbf4dd40de922f02c5f39e12b7ca7d2))


### Bug Fixes

* **inheritance:** validate protected drift against child base ([#164](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/164)) ([001a3ed](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/001a3ed10eaaf14a9d209827479acd8f4a4e1ce5))

## [1.6.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.5.4...v1.6.0) (2026-08-08)


### Features

* **inheritance:** apply single-PR finalization ([#162](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/162)) ([17a7b01](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/17a7b0135f78ac912f43c16a47b61882f6213693))
* **inheritance:** plan exact-source finalization ([#161](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/161)) ([f8a61b1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/f8a61b12a3866996c388dcfef57eb0adbc5dafaa))

## [1.5.4](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.5.3...v1.5.4) (2026-08-08)


### Bug Fixes

* **release:** upgrade release-please to Node 24 ([#157](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/157)) ([3caa730](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/3caa730c9f7a24e63b042a39c7c8c7af6cf30d4d))

## [1.5.3](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.5.2...v1.5.3) (2026-08-02)


### Bug Fixes

* **release:** attach SBOM to created release ([#155](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/155)) ([d229c43](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/d229c43872098b64719bcf43be2fcfeeaf112416)), closes [#154](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/154)

## [1.5.2](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.5.1...v1.5.2) (2026-08-02)


### Bug Fixes

* **inheritance:** keep fleet artifacts inside inherited roots ([#149](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/149)) ([919508c](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/919508cd851068b2baea5ebdf2abb287226a373c))
* **scorecard:** call verified actions directly ([#152](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/152)) ([ef70594](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/ef705940bd92ad059f07a7077e80b80620ae6413))

## [1.5.1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.5.0...v1.5.1) (2026-08-01)


### Bug Fixes

* **inheritance:** audit complete configured fleet ([#147](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/147)) ([cf4ebed](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/cf4ebed1422977adc15efb595ccedf479f0f0d7c))
* **inheritance:** tolerate pending protected ports ([#144](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/144)) ([c3b5dbf](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/c3b5dbf33761282e4657a25382892892604001cd)), closes [#143](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/143)

## [1.5.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.4.1...v1.5.0) (2026-08-01)


### Features

* **inheritance:** expose manual transport boundaries ([#136](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/136)) ([5fdc09e](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/5fdc09e61b959171b91312bd3b7dedc6bbe0bfad))
* **inheritance:** report fleet propagation boundaries ([#131](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/131)) ([a2c647a](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/a2c647a605b10a63c970cd4799d9a3d4c6b796bb))

## [1.4.1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.4.0...v1.4.1) (2026-07-30)


### Bug Fixes

* **inheritance:** scope adapter assertions to foundation root ([#128](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/128)) ([db11be9](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/db11be9e8e621605ad9d27b680dbfde80305cbcb))

## [1.4.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.3.0...v1.4.0) (2026-07-29)


### Features

* **inheritance:** add foundation agent entry contract ([#120](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/120)) ([13bacb5](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/13bacb5d5fcf4100e7bbef129a6d7155a7764597))
* **inheritance:** validate ordered agent profiles ([#118](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/118)) ([843bd86](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/843bd866d82948963c9ee021589d95b933ba3098))

## [1.3.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.2.1...v1.3.0) (2026-07-29)


### Features

* **ai:** route project maintenance rules conditionally ([#109](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/109)) ([3d8a65b](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/3d8a65ba7267b970ee4fc10999019520d17710b5))


### Bug Fixes

* **docs:** point DOC-014 to its current authority ([#112](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/112)) ([9962904](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/996290402085e30224451a9916b76cab5bf2f6d5))

## [1.2.1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.2.0...v1.2.1) (2026-07-28)


### Bug Fixes

* **ai:** preserve descendant entry contracts ([#99](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/99)) ([f4ca3f1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/f4ca3f1f0ded291e9ad7051c67630052e8ba2e85))

## [1.2.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.1.0...v1.2.0) (2026-07-28)


### Features

* **ai:** enforce context route budgets ([#89](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/89)) ([957b642](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/957b6429fe96d80b5322e5cc00230289aea97f23))
* **ai:** strengthen context safety checks ([#92](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/92)) ([ecc0762](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/ecc0762049f1dbe0a446eb97a057d6ab5a3fd14a))

## [1.1.0](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.0.1...v1.1.0) (2026-07-28)


### Features

* **ai:** bound context acquisition routes ([#88](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/88)) ([14ba217](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/14ba2171692e0657df8a5c265b71e005f91bae70))
* **docs:** enforce root README ownership ([#84](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/84)) ([a5e41d2](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/a5e41d25cf3865cc886f503d1c9edcdbc40f7f54))

## [1.0.1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/compare/v1.0.0...v1.0.1) (2026-07-28)


### Bug Fixes

* **ci:** exclude lockfiles from PR size limits ([#75](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/75)) ([c1f5d79](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/c1f5d797a76779a76282e34ce2fe87c4d176cc90)), closes [#74](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/74)
* **sync:** accept multi-language CodeQL matrices ([#73](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/73)) ([d9f1fe1](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/d9f1fe1e34f53e868e48938ab314d7cf05b189f5))

## 1.0.0 (2026-07-26)


### ⚠ BREAKING CHANGES

* **requirements:** downstream references to `docs/requirements/README.md` or `docs/templates/` must use the new `docs/foundation/` paths. Existing downstream repositories must append the documented `.templatesyncignore` exception once before running Template Sync.
* **governance:** `scripts/setup-github.sh` requires an explicit repository target; apply also requires the same value after `--confirm-repo`.

### Features

* **catalog:** add worked example module (Clean Architecture + DDD) ([#3](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/3)) ([ae20e80](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/ae20e80459075fa0dbe6ccd461663f27f2d4bc79))
* **claude:** add read-only code-reviewer subagent ([#12](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/12)) ([d5236aa](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/d5236aaaacfc7d210616263da5215510f5a88df3))
* **governance:** add deterministic state comparison ([#23](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/23)) ([2be91ac](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/2be91acb0c51ba77c7140e3167282e4b4eb2bf4a))
* **governance:** add inherited policy validation ([#21](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/21)) ([8035bbb](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/8035bbbf28c2ea1f84e7e5bfe90fb858c5370daf))
* **governance:** add read-only GitHub discovery ([#22](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/22)) ([dd04113](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/dd04113cc244e4714156e8c95658eb7204d610e8))
* **governance:** add template profile chain ([#37](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/37)) ([9ab0600](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/9ab06004ed129d0d27e4a1876aa03b04d067cc71))
* **governance:** add verified apply execution boundary ([#27](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/27)) ([67d1596](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/67d159630daa70d71c5ebb01b4200a394e4b11c4))
* **governance:** adopt solo-friendly defaults ([#34](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/34)) ([5632f8d](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/5632f8d81e3c6e2697d129e38c4113cdbd94874c))
* **governance:** enforce vulnerability intake controls ([#29](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/29)) ([d4c284c](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/d4c284c263b7a5b27034288b46558850c79913ae))
* **governance:** expose confirmed apply command ([#28](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/28)) ([70ea07a](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/70ea07add78ea3a80e75d790cb08e6dd43977111))
* **governance:** expose plan and audit commands ([#24](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/24)) ([86b3f4b](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/86b3f4bb0ef55fe658f1294de38bca85118d7b6c))
* **governance:** migrate setup to policy wrapper ([#31](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/31)) ([91276b9](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/91276b970805c550ee3d3fc929f0f0980af15681))
* **governance:** model repository collaboration settings ([#30](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/30)) ([cce70e4](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/cce70e4d4f8ad7695dbbc70e2f162200d83bc2e0))
* **governance:** plan deterministic apply actions ([#25](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/25)) ([9411ad6](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/9411ad67e2e5254c18cc1480da2db64d812c9ab0))
* **governance:** preserve stricter ruleset constraints ([#26](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/26)) ([64f6fc8](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/64f6fc82de3f7269a96ac534dde8c7ef9093b124))
* **inheritance:** plan next parent commit ([#36](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/36)) ([1e99d39](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/1e99d395ff949a40d45d888f59a6da41fc86e502)), closes [#32](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/32)
* **inheritance:** validate child-owned contract ([#35](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/35)) ([4035dbd](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/4035dbd0e3e7cca1300f1c2f8e49967e60940022))
* **skills:** interrogation phase in requirements + native skill wrappers ([#9](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/9)) ([d4df453](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/d4df4534107070f98dd581d4063ceeff60df9802))


### Bug Fixes

* **docs:** make foundation checks portable ([#52](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/52)) ([a177d1f](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/a177d1f694d6e754588c0753fb6ddf188753a8ea)), closes [#51](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/51)
* **governance:** recognize ruleset-only protection ([#57](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/57)) ([01eb97c](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/01eb97c6a7fd8106bada2be835803b49f56dce10))
* **hooks:** exempt explicit floating-tag moves from GR-011 force-push block ([#16](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/16)) ([7012f04](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/7012f04f57aa62ae678e28aceffbf19b3bd63848))
* **profiles:** restore terraform-gcp clean/doctor targets ([#5](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/5)) ([4af937c](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/4af937c84e1f17996207eca3bc16ba4d19cf8b43))
* resolve audit findings in guardrails, Makefiles, and CI config ([53d7910](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/53d7910dc4f696a76c45256e41d1c98d91bec7bc))
* **security:** configure CodeQL language matrix ([#64](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/64)) ([0c6d140](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/0c6d140a5247d4a8cfc348da4a56074291346ead))
* **sync:** enforce reviewed parent propagation ([#54](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/54)) ([ebd069d](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/ebd069de322ae6dd36d72ffd561fda249363dfd2))
* **sync:** keep PR body inside workflow script ([#62](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/62)) ([937baa4](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/937baa4e04d0bbe451c8bf04f5619db8bd3f5db0))
* **sync:** validate child contract in doctor ([#55](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/55)) ([86eb924](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/86eb9243a5ea1d1696588bceb1573afdfe182ce9))
* **template-sync:** use pathspec docs exclusions ([#50](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/50)) ([d9419c8](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/d9419c87133eb8d97d930aea98889224c2253a68))


### Documentation

* **requirements:** separate foundation-owned artifacts ([#40](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/40)) ([2c80552](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/commit/2c8055200e39d8eb3c77ee12261700b67ba546f1))
