---
id: ai-instruction-files-ja
title: AI指示ファイル・ガイド（日本語）
updated: 2026-09-13
---

# AIへ指示を出すファイル群ガイド（日本語）

このリポジトリには、AIエージェント（Claude Code / ChatGPT / Gemini / Codex など）の
振る舞いを「指示・案内・制約」するファイルが多数あります。本書はそれら**すべて**について、
**利用目的 / 利用シーン / 利用しないシーン / 利用例**を日本語でまとめた早見リファレンスです。

> ADR-0008で明示的に認められた、人間向けの日本語foundation文書です。各ファイルの
> **内容の正**は元ファイル自身です。矛盾があれば元ファイルが優先します。

## 0. 全体像 — 3層 + 補助

```
┌─ 薄い入口アダプター ────────────────────────────────────┐
│ CLAUDE.md（Claude Code）/ AGENTS.md（他エージェント）   │  ← まずここを読む
└───────────────┬───────────────────────────────────────┘
                │ agent profileのinputsを順番に読込
┌─ 継承契約 + project overlay + ルール本体（.ai/）─────────┐
│ guardrails > security > 読込済み契約/入口 > その他 .ai/ > docs/ │  ← 唯一の「正」
│ contracts（基盤/template）+ project + README（routing）  │
└───────────────┬───────────────────────────────────────┘
                │ タスク種別で選ぶ
┌─ 手順書（.skills/）─────────────────────────────────────┐
│ feature / bugfix / refactor / ... 各タスクの実行手順      │
└───────────────────────────────────────────────────────┘

  補助: .claude/（Claude固有の自動強制）, docs/foundation/adr/（基盤の意思決定）,
        MODULE.md（モジュール契約）, Issue/PRテンプレート（AIへの構造化入力）,
        ~/.claude・~/projects/CLAUDE.md（全リポ共通のグローバル指示）
```

**優先順位（矛盾時に強い方）**：`guardrails.md > security.md > 読込済みagent契約 / CLAUDE.md / AGENTS.md > その他の .ai/*.md > docs/**`。矛盾は黙って解決せず、強い方に従い
人間へ報告します。

## 1. カテゴリ早見表

| カテゴリ | ファイル | 一言 |
| -- | -- | -- |
| 入口 | [CLAUDE.md](../../../CLAUDE.md), [AGENTS.md](../../../AGENTS.md) | 明示的なagent profileを読み込む薄いアダプター |
| 構成 | [agent-profile.json](../../../.github/inheritance/agent-profile.json) | 基盤・テンプレート・プロジェクト入力の順序付き一覧 |
| 継承契約 | [foundation contract](../../../.ai/contracts/foundation/README.md) | identity-freeな基盤指示とguardrail本体 |
| template契約 | `.ai/contracts/templates/<owner>/<repository>/` | 中間templateが直接の子へ公開する追加契約 |
| プロジェクト情報 | [agent-overlay.md](../../../.ai/project/agent-overlay.md) | 利用先固有の識別情報・役割・スタック |
| 条件付きproject文書規則 | [project-document-maintenance.md](../../../.ai/project-document-maintenance.md) | handoff・roadmap・root README・継承を扱う時だけ読む規則 |
| ルール索引 | [.ai/README.md](../../../.ai/README.md) | 優先順位・タスク別ルーティング表 |
| ルール本体 | [.ai/](../../../.ai/) の各 `*.md` | 分野別の正準ルール（ID付き） |
| 手順書 | [.skills/](../../../.skills/) の各 `*.skill.md` | タスク別の実行プレイブック |
| 自動強制 | [.claude/](../../../.claude/) | Claude Code のフック（即時ブロック/整形）・権限制御・ネイティブSkill |
| 意思決定 | [docs/foundation/adr/](../adr/)、`docs/adr/` | 基盤と利用先の「なぜ」を所有者別に記録 |
| 用語 | [docs/foundation/glossary.md](../glossary.md)、`docs/glossary.md` | 基盤と利用先プロジェクトの統一用語 |
| ソース構造 | [src/README.md](../../../src/README.md), [tests/README.md](../../../tests/README.md) | コード配置規約・MODULE.md雛形 |
| 方向性 | `docs/roadmap.md` | 利用先で何を作る/作らないかの指針 |
| 契約 | `src/modules/*/MODULE.md`, [profiles/README.md](../../../profiles/README.md) | モジュール/makeターゲットの契約 |
| 構造化入力 | [.github/](../../../.github/) の Issue/PR テンプレート | AIへの指示を型化 |
| グローバル | `~/.claude/CLAUDE.md`, `~/projects/CLAUDE.md` | 全リポ共通の好み（リポ外・Claude固有） |

______________________________________________________________________

## 2. 入口ファイル

### `CLAUDE.md`

- **利用目的**：全AIエージェント共通の、識別情報を持たない薄い入口アダプター。agent profileを検証し、宣言された契約とoverlayを順番に読み込む。
- **利用シーン**：セッション開始時に必ず全読。Claude Codeでは自動読込される。
- **利用しないシーン**：プロジェクト情報や詳細ルールの記述（profile入力側に置く）。タスク種別の判定（読込後の`.ai/README.md`を使う）。
- **利用例**：profileのfoundation入力、owner-qualified template入力、project入力を記載順に全文読込する。

### `AGENTS.md`

- **利用目的**：Claude以外のエージェント（ChatGPT/Gemini/Codex）の入口。`CLAUDE.md`アダプターへ誘導し、ランタイム機能の等価手段を示す。
- **利用シーン**：非Claudeエージェントにこのリポジトリを触らせるとき、最初に読ませる。
- **利用しないシーン**：Claude Code を使うとき（`CLAUDE.md` が自動で読まれるため不要）。
- **利用例**：ChatGPTに「まず`AGENTS.md`を読んで、その指示に従って」と指定 → profile入力を読み、フックが無い分、`make lint`を手動実行するなどの等価手段に読み替える。

### `.github/inheritance/agent-profile.json` と `.ai/project/agent-overlay.md`

- **利用目的**：profileはfoundation → template（親から子）→ projectの正確な構成順を宣言する。project overlayはリポジトリ識別情報、役割、スタックなど利用先固有の事実だけを持つ。
- **利用シーン**：新規利用先の初期化、継承親の変更、manifest schema version 2への移行時。どちらも子リポジトリの保護対象としてレビューする。
- **利用しないシーン**：profileに長いルール本文を複製する、project overlayで基盤のMUST・guardrail・security controlを弱める、`CLAUDE.md`へプロジェクト情報を埋め込む。
- **利用例**：テンプレートを継承するSaaSでは、基盤契約、テンプレートoverlay、SaaS自身のproject overlayを順番に列挙する。

### `.ai/contracts/foundation/` と `.ai/contracts/templates/<owner>/<repository>/`

- **利用目的**：foundation contractは全repositoryが継承するidentity-freeな指示を持つ。template
  contractは中間templateが直接の子へ公開するfamily/product追加契約をowner-qualified pathで持つ。
- **利用シーン**：agent profileが指定した個別pathだけを記載順に全文読み込む。中間templateを追加・
  変更するときは、直接親が公開したexportとprofile順序を検証する。
- **利用しないシーン**：directoryを再帰的に探索して未宣言の契約を読み込む、project固有情報を
  foundation contractへ置く、後段のoverlayでfoundationのMUSTを弱める。
- **利用例**：foundationの`agent-entry.md`を読み、次に
  `templates/<owner>/<parent>/agent-overlay.md`、最後にproject overlayを読む。

各namespaceの`inheritance-export.json`は子初期化用の機械可読metadataであり、agentへの文章指示では
ありません。継承path、profile、project overlayの所有境界と同期確定手順は
[継承契約](../../../.github/inheritance/README.md)を正とします。

______________________________________________________________________

## 3. 合成契約とルール本体（`.ai/`）

すべて**ID付き**（GR-/SEC-/ARC-/COD-/TST-/REL-/DOC-/REV-/WF-/LOG-）。コミットやレビューで
`「GR-010 違反」`のように一意参照します。

### `.ai/README.md`（索引・ルーティング）

- **利用目的**：`.ai/` の地図。優先順位（権威順）とタスク別の「読むべきファイル表」を提供。
- **利用シーン**：タスク開始時に「何を読むべきか」を決める。矛盾の解決順を確認する。
- **利用しないシーン**：具体的なルール内容そのものの参照（各ドメインファイルを見る）。
- **利用例**：「新機能」→ 表に従い workflow / architecture / coding-rules / testing + feature.skill を読み込む。

### ルール各ファイル（早見表）

| ファイル | 利用目的（何を規定） | 利用シーン | 利用しないシーン | 利用例 |
| -- | -- | -- | -- | -- |
| [guardrails.md](../../../.ai/guardrails.md) | 絶対禁止（GR）。指示でも覆せない | 全タスクの前提。破壊的操作の前 | 「推奨」レベルの判断（それは各ルール） | `curl\|sh` を実行しようとして GR-032 でブロック |
| [security.md](../../../.ai/security.md) | セキュリティ運用（SEC） | 認証/入力/秘密情報/依存を扱う時、レビュー、リリース | UIの見た目調整など非セキュリティ作業 | 新エンドポイント追加時に SEC-020（既定deny）を適用 |
| [architecture.md](../../../.ai/architecture.md) | 構造・層・依存方向（ARC） | 新機能、リファクタ、モジュール変更 | ドキュメントのみの修正 | domain から DB ドライバを import しようとして ARC-002 で回避 |
| [coding-rules.md](../../../.ai/coding-rules.md) | 命名・エラー処理・依存方針（COD） | コードを書く/直す全般 | 設計そのものの是非（architecture へ） | 3回目の重複で初めて抽象化（COD-020） |
| [testing.md](../../../.ai/testing.md) | テスト戦略・カバレッジ（TST） | テスト作成、バグ修正、リファクタ | 純粋なドキュメント変更 | バグ修正で「まず落ちる回帰テスト」を書く（TST-002）。新機能は1振る舞いずつ red → green で進め（TST-004）、期待値を実装と同じ計算で作らない（TST-010） |
| [workflow.md](../../../.ai/workflow.md) | タスクの進め方・コミット規約（WF） | ほぼ全タスク（intake→PR） | 単発の質問応答 | ブランチ名 `fix/207-null-avatar`、Conventional Commits（WF-020） |
| [release.md](../../../.ai/release.md) | バージョニング・リリース手順（REL） | リリース準備 | 通常の機能開発中 | `feat` コミットから MINOR を自動導出（REL-001） |
| [documentation.md](../../../.ai/documentation.md) | ドキュメント規約・更新マトリクス（DOC） | ドキュメント作成、機能変更に伴う更新 | コード内部だけの微修正 | API変更時に doc-update matrix で `docs/api/` 更新を判定（DOC-030） |
| [project-document-maintenance.md](../../../.ai/project-document-maintenance.md) | project状態・roadmap・root README所有権の条件付き規則 | handoff、roadmap、root README、onboarding、継承を扱う時 | 無関係な実装タスクの常時読込 | 継承初期化時にroot READMEの所有者を確認し、祖先READMEをnamespaced archiveへ保存（DOC-014） |
| [review-checklist.md](../../../.ai/review-checklist.md) | 10観点のレビュー基準（REV） | PRレビュー、PR前のセルフレビュー | 実装中の細かい判断 | セルフレビューで REV-SEC を走査し秘密混入を確認 |
| [mission.md](../../../.ai/mission.md) | プロジェクトの目的・成功基準 | 方向性の妥当性判断、オンボーディング | 日々の実装詳細 | 提案が mission の成功基準に沿うか照合 |
| [decision-log.md](../../../.ai/decision-log.md) | 意思決定の追記索引（LOG/ADR） | 設計変更前に「既に決まってないか」確認、変更後に追記 | 通常の実装 | LOG-0006「jq無しでもガードが動く」を読み、正規表現を安易に簡素化しない |

______________________________________________________________________

## 4. 手順書（`.skills/`）— タスク別プレイブック

各スキルは「目的 / 入力 / 手順 / 判断基準 / 出力 / チェックリスト」を持つ自己完結の手順書。
ルーティング表（`.ai/README.md`）で**タスクに一致した時だけ**読み込みます。

### [.skills/README.md](../../../.skills/README.md)

- **利用目的**：スキルの形式契約と一覧。Claude Code ネイティブ Skill 化の方法も記載。
- **利用シーン**：新しいスキルを追加/編集するとき、どのスキルがあるか俯瞰したいとき。
- **利用しないシーン**：実タスクの実行中（個別スキルを直接読む）。
- **利用例**：新スキル追加時に、必須セクション（目的/入力/…）の形式を確認。

### スキル早見表

| スキル | 利用目的 | 利用しないシーン | 利用例 |
| -- | -- | -- | -- |
| [requirements](../../../.skills/requirements.skill.md) | 何を作るかを要件定義（目的優先・ゼロベース・対話で決定を詰める） | 実装作業そのもの（featureへ） | 目的を1文で固定→決定を1つずつ推奨案付きで詰める（確定した用語はその場で `docs/glossary.md` へ）→FR/NFR採番→テンプレ記入 |
| [feature](../../../.skills/feature.skill.md) | 新機能を端から端まで実装 | 既存バグの修正（bugfixへ） | issue の受入基準を Definition of Done として実装 |
| [bugfix](../../../.skills/bugfix.skill.md) | 欠陥を堅牢・冪等な恒久修正で根本解決 | 新機能追加、純粋な整形 | 再現→落ちる回帰テスト→原因修正→再実行安全性→周辺捜索。明示指示時のみ期限付き応急処置 |
| [refactor](../../../.skills/refactor.skill.md) | 振る舞いを変えず構造改善 | 挙動を変える変更（featureへ） | 特性テストで固定→機械的に段階リネーム/抽出 |
| [architecture](../../../.skills/architecture.skill.md) | 構造/境界/技術の変更（ADR必須） | 局所的なコード修正 | 2〜4案（何もしない含む）比較→ADR→人間承認→段階移行 |
| [test](../../../.skills/test.skill.md) | テストの追加/改善/flaky修復 | 実装そのもの | 振る舞い列挙→境界マトリクス（空/1/多/最大/異常） |
| [security](../../../.skills/security.skill.md) | 脆弱性対応・堅牢化・監査 | 通常の機能実装 | スキャナ指摘の分類→信頼境界で修正→性質をテスト化 |
| [documentation](../../../.skills/documentation.skill.md) | ドキュメント作成/保守 | コードのみの変更 | doc-update matrix の義務を満たし、リンク/コマンドを実検証 |
| [review](../../../.skills/review.skill.md) | PRレビュー/セルフレビュー | 実装作業そのもの | 10観点を走査し Blocker>Major>Minor で file:line+ID+修正案 |
| [release](../../../.skills/release.skill.md) | リリース準備（人間が承認） | 日常開発 | REL-020 ゲート検証→リスク要約→**マージは人間** |

- **スキル全体を使わないシーン**：会話的な単発質問、些末な機械的編集（スキルを読むまでもない場合）。

______________________________________________________________________

## 5. Claude Code 固有の自動強制（`.claude/`）

「コンテキストとしての指示」ではなく、**実際にコマンドを止める/実行する**強制層です（Claude Code のみ）。

### [.claude/settings.json](../../../.claude/settings.json)

- **利用目的**：フックの登録（PreToolUse ガード／PostToolUse 整形）と権限制御。`permissions.deny` で `.env` 等の読取拒否、`permissions.allow` で**非変更の読取専用コマンド**（`make doctor/lint/test`・読取系 git など）を事前許可し確認プロンプトを削減。`deny` が `allow` に優先。
- **利用シーン**：Claude Code セッション中、常時自動適用（あなたが意識する必要はない）。
- **利用しないシーン**：他エージェント（読まれない）。挙動を変えたい時は編集するが、`.local.json` は個人用。
- **利用例**：ファイル編集後に自動で `make format`/`make lint` が走り、失敗はエージェントへフィードバックされる。`make test` は事前許可済みなので確認なしで実行、`make format`（変更を伴う）は引き続き確認される。

### [.claude/skills/](../../../.claude/skills/)（ネイティブ Skill ラッパー）

- **利用目的**：`.skills/*.skill.md` を Claude Code のネイティブ Skill として公開し、`/requirements` のように直接呼び出せるようにする薄いラッパー（`<name>/SKILL.md`）。中身は frontmatter ＋「`.skills/<name>.skill.md` を読んで従え」の1行のみで、手順の本体は `.skills/` が唯一の正。
- **利用シーン**：Claude Code でスキルをコマンド的に起動したいとき。
- **利用しないシーン**：他エージェント（ラッパーを無視し、ルーティング表経由で `.skills/` を直接読む）。ラッパーに手順を複製すること（正の二重化になる）。
- **利用例**：`/requirements` で要件定義スキルを起動 → 実体の `.skills/requirements.skill.md` の手順が実行される。新スキル追加時は同PRで対応するラッパーも追加する。

### [.claude/hooks/guard-bash.sh](../../../.claude/hooks/guard-bash.sh)

- **利用目的**：ガードレール違反の Bash コマンドを実行前にブロック（GR-010/011/012/031/032）。
- **利用シーン**：Claude Code が Bash を実行する度、自動で通過チェック。
- **利用しないシーン**：手動で回避してはいけない（GR-012）。他エージェントでは AGENTS.md の等価手段（実行前に自己チェック）。
- **利用例**：`git push origin main` → exit 2 でブロックし「PRを作れ」と提示。`rm -rf /etc` もブロック。

### [.claude/hooks/post-edit-quality.sh](../../../.claude/hooks/post-edit-quality.sh)

- **利用目的**：Edit/Write の後に対象ファイルを自動 format + lint（COD-001）。
- **利用シーン**：コード編集の直後に自動。
- **利用しないシーン**：Markdown 等の非コード（スキップされる）。テンプレート状態では Makefile が no-op のため実質何もしない。
- **利用例**：`.py` を編集 → 自動整形、lint 失敗ならエージェントへ「先に直せ」と返る。

### [.claude/hooks/tests/guard-bash.test.sh](../../../.claude/hooks/tests/guard-bash.test.sh)

- **利用目的**：ガードの block/allow マトリクス全ケースを固定する回帰テスト（`make doctor` と CI が実行）。
- **利用シーン**：ガードの正規表現を変更した時、CI/doctor で自動検証。
- **利用しないシーン**：通常の開発中に手動で気にする必要はない。
- **利用例**：ガードを直したら `bash .claude/hooks/tests/guard-bash.test.sh` で全件パスを確認。

### [.claude/agents/code-reviewer.md](../../../.claude/agents/code-reviewer.md)（レビュー特化サブエージェント）

- **利用目的**：現在の差分を10観点チェックリストでレビューする読み取り専用サブエージェント。WF-090 のセルフレビューを操作可能にする。観点・手順の本体は `.ai/review-checklist.md` と `.skills/review.skill.md` が正典で、定義は薄い参照のみ。
- **利用シーン**：PR作成前のセルフレビュー、または差分レビューを依頼するとき。
- **利用しないシーン**：ファイルの編集（読み取り専用・編集/コミット/pushはしない）。他エージェント（サブエージェントはClaude Code固有 → 等価には `.skills/review.skill.md` を直接読む）。
- **利用例**：`code-reviewer` サブエージェントを起動 → `git diff` で対象を特定 → Blocker>Major>Minor で `file:line`＋ルールID＋修正案を報告（PRの改変はしない）。

______________________________________________________________________

## 6. 意思決定・用語・方向性（利用先の docs/）

### [docs/foundation/adr/](../adr/) と `docs/adr/`（ADR）

- **利用目的**：基盤の受理済み決定は `docs/foundation/adr/`、利用先固有の決定は `docs/adr/` に不変記録する（GR-022）。
- **利用シーン**：構造/境界/技術の変更前に両方を確認し、利用先の新決定は `docs/adr/` に起票。
- **利用しないシーン**：局所的な実装判断（それは decision-log の1行や why コメントで足りる）。
- **利用例**：[0002](../adr/0002-ai-facing-docs-in-english.md)を読み基盤の言語方針を理解。利用先の新規ADRは [ADRテンプレート](../templates/adr.md) を `docs/adr/` へ複製。

### [docs/foundation/glossary.md](../glossary.md) と `docs/glossary.md`（統一用語）

- **利用目的**：基盤の再利用語と、利用先プロジェクト固有のユビキタス言語を所有者別に定義する（COD-002）。
- **利用シーン**：新しい概念に名前を付ける前に両方を確認し、プロジェクト固有語は `docs/glossary.md` に同PRで追記。
- **利用しないシーン**：一般的な技術用語（ここは「このプロジェクト固有の語」）。
- **利用例**：「Contract change」と「breaking change」の違いを glossary で確認して用語を統一。

### `docs/roadmap.md`（利用先の方向性）

- **利用目的**：利用先プロジェクトの進む方向とマイルストーン。新規作成時は [roadmapテンプレート](../templates/roadmap.md) を使う。
- **利用シーン**：機能提案の妥当性判断、優先順位の把握。「Now / Next / Later / 対象外」を確認。
- **利用しないシーン**：日々の作業キュー（それは GitHub の issue/milestone）。"Later" 項目の先回り実装（COD-051 で禁止）。
- **利用例**：提案が roadmap の「対象外」に該当すると分かり、着手せず理由を添えて差し戻す。

______________________________________________________________________

## 7. ソース構造と契約（`src/modules/*/MODULE.md`）

- **利用目的**：モジュールの公開API・所有データ・不変条件・依存を1ページで宣言（ARC-003）。
- **利用シーン**：そのモジュールを変更する前に必ず読む。契約が変わったら同PRで更新。
- **利用しないシーン**：他モジュールの内部実装を知りたい時（内部は非公開。公開APIのみ参照）。
- **利用例**：`src/modules/catalog/MODULE.md` が存在するリポジトリでは、公開API
  `AddProduct.handle` と不変条件を把握してから改修。

### [src/README.md](../../../src/README.md) / [tests/README.md](../../../tests/README.md)（配置規約）

- **利用目的**：ソース/テストの配置規約と `MODULE.md` の雛形を示す構造ガイダンス（ARC-001）。
- **利用シーン**：新モジュール作成、ファイルの置き場所を決めるとき、`MODULE.md` を新規作成するとき。
- **利用しないシーン**：既存モジュール内の局所修正で構造が変わらないとき。
- **利用例**：新機能の置き場所をレイアウト図で確認し、`tests/` が `src/` を鏡写しにする規約（TST-001）に従う。

### [profiles/README.md](../../../profiles/README.md)（正準ターゲット契約）

- **利用目的**：`make` 正準ターゲット（setup/format/lint/test/…/doctor）の**拘束力ある意味論**を定義。読込済みfoundation契約が参照。
- **利用シーン**：`make` ターゲットの挙動を確認するとき、スタック別プロファイル（Makefile）を追加/編集するとき。
- **利用しないシーン**：特定スタックの具体コマンドそのもの（各 Makefile 実装を見る）。
- **利用例**：`lint` は「チェック専用・自動修正しない」という契約を確認し、lint に fmt を混ぜない。

______________________________________________________________________

## 8. 構造化入力（`.github/` テンプレート）

AIへ「指示を出す」ための入力を型化するファイル群。人間が埋めた内容がAIの作業指示になります。

### Issue テンプレート（[.github/ISSUE_TEMPLATE/](../../../.github/ISSUE_TEMPLATE/)）

- **利用目的**：バグ/機能/セキュリティ課題を、AIがそのまま着手できる形（受入基準・再現手順）で受け取る。
- **利用シーン**：新しい作業を起票するとき。`feature_request` の受入基準 = AIの Definition of Done。
- **利用しないシーン**：脆弱性の詳細（公開Issue禁止 → 非公開のセキュリティ報告へ）。
- **利用例**：`bug_report.yml` の再現手順がそのまま回帰テストの素になる。

### [PULL_REQUEST_TEMPLATE.md](../../../.github/PULL_REQUEST_TEMPLATE.md)

- **利用目的**：PRに必要な情報（変更分類・テスト・依存の正当化・AI開示・セルフレビュー）を型化。
- **利用シーン**：AIがPRを作成するとき、全セクションを埋める。
- **利用しないシーン**：ドラフトの下書き段階（ただしマージ前には必須）。
- **利用例**：依存を追加したら Dependencies 表に目的・代替・ライセンスを記入（GR-023）。

______________________________________________________________________

## 9. グローバル層（リポジトリ外・Claude Code 固有）

Claude Code は起動時に**親ディレクトリを遡って** `CLAUDE.md` を読み込みます。全リポ共通の指示を効かせられます。

| 場所 | 利用目的 | 利用シーン | 利用しないシーン | 利用例 |
| -- | -- | -- | -- | -- |
| `~/.claude/CLAUDE.md` | 全プロジェクト共通の個人設定 | 「常に日本語で応答」等の恒常的な好み | ハードなガードレール（失われる） | 応答言語・コミット文体を指定 |
| `~/projects/CLAUDE.md` | その配下の全リポ共通ハウスルール | 複数リポをまとめる作業ディレクトリ | リポ固有の正準ルール（各 .ai/ が持つ） | 優先ライブラリ・役割分担を記述 |

- **重要**：これは Claude Code 固有。ChatGPT/Gemini は親/グローバル `CLAUDE.md` を読みません。
  **ハードな禁止事項は各リポの `.ai/` と PreToolUse フックに置く**こと（グローバル層“だけ”に置くと、
  他所へcloneした/他エージェントが読むリポで失われる）。詳細は [usage.ja.md](usage.ja.md) の Q2。

______________________________________________________________________

## 10. エージェント別の使い分け

|  | Claude Code | ChatGPT / Gemini / Codex |
| -- | -- | -- |
| 入口 | `CLAUDE.md`（自動読込）→ agent profile | `AGENTS.md` → `CLAUDE.md` → agent profileを明示的に読ませる |
| ルール/スキル | 同じ（`.ai/`, `.skills/`） | 同じ（プレーンMarkdownなので読める） |
| 自動強制 | `.claude/` フックが自動で効く | フックは効かない → `make lint` 等を手動実行、GR を自己チェック |
| グローバル層 | `~/.claude`・親 `CLAUDE.md` 自動 | 読まれない → 必要なら手動で貼る |

______________________________________________________________________

## 11. よくある落とし穴

- **ハードルールをグローバル層だけに置く** → 他エージェント/他リポで失われる。`.ai/` とフックに置く。
- **`.claude/` を他エージェントに期待する** → 読まれない。等価手段（手動 lint・自己チェック）を使う。
- **入口アダプターだけ読んでprofile入力を省略する** → 基盤契約やプロジェクト情報が欠ける。記載順に全入力を読む。
- **プロジェクト情報を`CLAUDE.md`へ複製する** → 継承時に衝突する。`.ai/project/agent-overlay.md`へ置く。
- **`CLAUDE.md` は強制ではない**（公式明記）。確実に止めたい操作は PreToolUse フックで実装する。
- **フックを手動回避する（`--no-verify` 等）** → GR-012 違反。原因を直す。

______________________________________________________________________

関連：新環境セットアップ手順は [usage.ja.md](usage.ja.md)、`.ai/` の索引は
[.ai/README.md](../../../.ai/README.md)、継承PRの確定・fleet監査・private access境界は
[継承契約](../../../.github/inheritance/README.md)、基盤の決定の経緯は
[docs/foundation/adr/](../adr/) を参照。

______________________________________________________________________

## 12. 意図的に除外したファイルと、その理由

本書は「主目的がAIの振る舞いを**指示・案内・制約**すること」を収録基準にしています。以下は基準から外れるため
意図的に除外しました（AIが"使う/従う"対象ではあっても、指示文そのものではない）。

| グループ | ファイル | 除外理由 |
| -- | -- | -- |
| ツール/自動化 | `Makefile`, `profiles/*/Makefile`, `.pre-commit-config.yaml`, `.github/workflows/*`, `scripts/*.sh`, `renovate.json` | 実行インターフェースや強制機構であって挙動の"指示文"ではない（正準ターゲットの契約 = profiles/README.md は §7 に収録） |
| 設定 | `.gitignore`, `.gitattributes`, `.editorconfig`, `.env.example`, `.mdformat.toml`, `.templatesyncignore` | 環境・整形・同期の設定 |
| ガバナンス metadata | `.github/CODEOWNERS`, `labels.yml`, `discussion-categories.md` | レビュー経路・ラベル・カテゴリ定義。AIは使うが指示ではない |
| 人間向け | `README.md`, `SECURITY.md`, `docs/foundation/guides/usage.md`, `usage.ja.md` | 人間向け。特に `README.md` はAIを「CLAUDE.mdへ」と誘導する側。AI向けセキュリティは `.ai/security.md`（§3収録）が担う |
| 記述的ドキュメント | `docs/foundation/guides/*.md` | 権威レベル5の**記述（informative）**。利用先所有の`docs/**`を占有せず、各配置先の目的・構造・更新トリガーを案内する |
| ドキュメント雛形 | `docs/foundation/templates/` | 基盤所有の記入用テンプレート（例：`requirements.md`）。指示文ではなく、`requirements` スキルが利用先の `docs/` へ展開する対象。文章規約は DOC-002、文書構造は DOC-003（ともに§3収録）が担う |
| 例コード | `src/modules/catalog/**/*.py`, `tests/**/*.py` | "指示"ではなく"手本（imitateする参照, COD-050）"。契約は代表として `MODULE.md` を §7 に収録 |

**線引きの原則**：規範（normative, 従うべき）は収録、記述（descriptive, 参考情報）と純粋な実行/設定は除外。
記述的docsやツールも間接的にAIの行動に影響しますが、"指示の発生源"は `.ai/`・`.skills/`・契約ファイルに集約されています。
