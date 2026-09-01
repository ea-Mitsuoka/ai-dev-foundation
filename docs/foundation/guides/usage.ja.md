---
id: usage-ja
title: 使い方（日本語）— 新しいPC / 別アカウント / 新規プロジェクト
updated: 2026-08-30
---

# 使い方（日本語セットアップ手順書）

> English: [usage.md](usage.md) ／ このファイルはADR-0008で明示的に認められた、人間向けの
> 日本語foundation文書です。内容が英語版と食い違った場合は**英語版が正**です。

新しいPCや別のGitHubアカウントで基盤を使うときの手順。**まず2つのシナリオのどちらかを判断**
してください。手順が変わります。

| シナリオ | やりたいこと | 使うもの |
|----------|--------------|----------|
| A | この基盤の上で**新規プロジェクトを作る** | GitHub の **「Use this template」**（`git clone` ではない）|
| B | **この基盤リポジトリ自体**を別マシンで開発継続する | `git clone` |

`git clone` が正解なのはシナリオBだけです。シナリオAでcloneすると、新規プロジェクトにこの基盤の
履歴とプレースホルダが混入します。テンプレート機能を使ってください。

---

## シナリオA — テンプレートから新規プロジェクトを作る

現在必要な契約に基づいて親を選び、明示的な継承情報を初期化します。

### 1. 直接の親テンプレートを選ぶ

リポジトリの**主要な成果物**に現在適用される契約を公開している、最も近い保守中の
テンプレートを選びます。

| 現在のリポジトリの役割 | 直接の親 |
|--------------------------|----------|
| 適用可能な保守中の特化テンプレートがない一般プロジェクト | `ea-Mitsuoka/ai-dev-foundation` |
| Terraformで管理するGoogle Cloud基盤が主要成果物で、Terraform family overlayと`iac-scan`が必要 | `ea-Mitsuoka/terraform-gcp-template` |
| Next.js SaaS applicationに保守中のNext.js familyとSaaS template契約が必要 | `ea-Mitsuoka/nextjs-saas-template` |
| 現在必要なfamilyまたはproduct契約を別の保守中テンプレートが公開している | その中間テンプレート |

TerraformやGoogle Cloudを付随的に使うだけでは`terraform-gcp-template`を選びません。
同様に、Next.jsを使うだけでは`nextjs-saas-template`を選びません。保守中のfamily/product契約が
現在のrepositoryへ適用されることが条件です。将来使うかもしれない機能を理由に親を選びません。
直接の親による来歴とfamily overlayを維持するため、適用可能な中間テンプレートを飛ばさないでください。

### 2. 選んだテンプレートから新リポジトリを作成

Web: テンプレートリポジトリを開く → **Use this template** → **Create a new repository**。

CLI（同等）:
```bash
gh repo create <あなたのアカウント>/<新プロジェクト> \
  --template <選んだowner>/<選んだparent> \
  --private --clone
cd <新プロジェクト>
```
これで**クリーンな履歴**の新リポジトリがあなたのアカウント配下にできます。

作成時点の親の40文字commitを記録してください。後から、生成元ではない新しいbranch先端へ
証跡を置き換えてはいけません。

### 3. 継承情報とリポジトリ所有権を確立

次を1つのレビュー付き初期化PRで完了します。

1. `.github/inheritance/manifest.json`の親を選択した直接の親に設定し、全pathを
   inherited、protected、意図的なunownedに分類します。schemaは
   [継承契約](../../../.github/inheritance/README.md)を参照してください。
2. `.github/inheritance/lock.json`を作成に使用した親commitへ固定します。
3. `.github/inheritance/agent-profile.json`をfoundation、適用する中間templateの
   parent-to-child順、当該repositoryのproject入力の順に設定します。
   `.ai/project/agent-overlay.md`とprofileはprotectedにします。
4. コピーされたroot READMEを置き換える前に
   `docs/inheritance/readmes/<owner>/<repository>.md`へ保存し、rootの所有者markerを新しい
   `OWNER/REPOSITORY`へ変更します（DOC-014）。
5. `.templatesyncignore`で全protected rootと全workflowを保護します。リポジトリ固有の
   追加除外は許可されるため、2つのlistは完全一致である必要はありません。
6. 定期PR作成を有効にする前にローカル検証します。

```bash
make doctor
python3 scripts/template_inheritance.py validate --root .
python3 scripts/template_inheritance.py plan \
  --root . --parent-root ../<選択した親のworktree>
```

初期化PRがgreenでmergeされた後、workflowから直接親を読み取れるrepositoryだけ、日次の
レビュー付き同期へopt-inします。

```bash
gh variable set TEMPLATE_SYNC_ENABLED --body true
```

直接親がprivateの場合、protected workflowへ承認済みの認証分離実装を移植し、
[Issue #178](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/178)の限定pilotがその継承関係で
完了するまで、この変数を無効のままにしてください。設定・pilot・鍵rotation・rollbackの正準手順は
[private直接親の認証](../../../.github/inheritance/README.md#authenticate-a-private-direct-parent)に集約します。
認証の回避策としてrepositoryをpublicへ変更してはいけません。

中間templateを親にした場合、agent profileへowner-qualified template overlayを必ず含めます。
伝播は親から子へ、merge済みの1 hopずつ進みます。

### 3.1. 各同期PRをレビューして確定

Template Syncはsingle-flightです。1つのrepositoryでopenにできる
`chore/template_sync_*` PRは1件だけです。後続の定期実行や手動実行は重複PRを作らず、既存PRを
報告します。open中に親へ追加された変更は、そのPRのmerge後に収集されます。

同期branchで直接親の正確なsourceと継承差分をレビューし、ローカルの`finalize-sync` previewを
実行します。`ready_to_finalize`の場合だけapplyし、対応済みの手動境界とlock更新を同じPRへ
まとめます。この処理はcommit、push、merge、GitHub API、governance変更を行いません。
正準コマンドとblockerの意味は
[継承契約](../../../.github/inheritance/README.md#plan-single-pr-finalization)を参照してください。

各PRには通常のCIと人間のレビューが必要です。中間templateをmergeしてからその直接の子を同期し、
hopを飛ばしたりauto-mergeしたりしないでください。

### 4. テンプレートのプレースホルダを置換

カスタマイズ対象はすべて `{{...}}` トークンです。全部洗い出す:
```bash
grep -rn "{{" . --exclude-dir=.git
```
最低限置換するもの: `.ai/mission.md` の `{{...}}`、`.github/CODEOWNERS`・
`.github/ISSUE_TEMPLATE/config.yml`・`.github/workflows/template-sync.yml` の `{{ORG}}`、
Pythonプロファイルを使うなら `{{PACKAGE}}`。

プロジェクトの識別情報とスタック情報は `CLAUDE.md` に書きません。新しいリポジトリに合わせて
`.ai/project/agent-overlay.md` を更新してください。
`.github/inheritance/agent-profile.json` は基盤入力を維持し、最後のproject入力の
`repository`だけを新しい`OWNER/REPOSITORY`へ変更します。子の継承manifestを追加するときは、
agent profileとproject overlayを保護対象にしてください。

### 5. CODEOWNERS をアカウント種別に合わせて修正

`.github/CODEOWNERS` は既定で**チーム記法**（`@{{ORG}}/maintainers`）です。チームは
**GitHub Organization にしか存在しません**。**個人アカウント**ではユーザー名に置換してください:
```
*   @your-username
```
個人リポジトリにチーム記法を残すと、CODEOWNERS が**黙って無効化**されます
この判定は互換ラッパーの対象外なので、ガバナンス適用前に修正してください。

### 6. Makefile プロファイルを選ぶ

最も近いリファレンス実装をルートにコピーしてスタックに合わせます:
```bash
cp profiles/python-uv/Makefile ./Makefile      # または typescript-node / terraform-gcp
```
正準ターゲット契約は [profiles/README.md](../../../profiles/README.md) を参照。
インスタンス化後は、必須ターゲットにテンプレートの `not wired yet` 実装が残っていると
`make doctor` が失敗します。対象外のターゲットは、たとえば
`[project] build: not applicable — no deployable artifact` のように、利用先が所有する
明示的な対象外結果へ置き換えてください。テンプレートのプレースホルダーは残しません。

### 7. GitHub ガバナンスを点検

```bash
python3 scripts/github_governance.py validate --root .
python3 scripts/github_governance.py plan --root . --repo OWNER/REPOSITORY
python3 scripts/github_governance.py audit --root . --repo OWNER/REPOSITORY
python3 scripts/github_governance.py apply --root . --repo OWNER/REPOSITORY \
  --confirm-repo OWNER/REPOSITORY

# 同じplan/apply経路を使う互換入口:
DRY_RUN=1 bash scripts/setup-github.sh OWNER/REPOSITORY
bash scripts/setup-github.sh OWNER/REPOSITORY --confirm-repo OWNER/REPOSITORY
```

`validate` はオフラインで動作し、foundation、`.github/governance/profiles/`内の単一
profile chain、repository policyを自動的に解決します。required checksは単調合成され、
profileとrepository policyはcheckを追加できますがfoundation checkを削除できません。
`plan` と `audit` は認証済みのGET-only
`gh api` を使用し、同じ秘匿化済みJSON比較を出力します。対象branch先端で必要check名が
観測されない場合はdriftとし、無関係なcheckはdriftにしません。`plan` は比較完了時に0、
`audit` はdriftまたは権限不足によるunknown時に1、policy・入力・GitHub読み取りの失敗時には
どちらも2を返します。

`audit`が1で終了した場合の対処は
[GitHubガバナンスのトラブルシューティング](../troubleshooting/github-governance.md)を参照してください。

リポジトリのidentityが変わったとき — 譲渡、別アカウントへの移動、bootstrap exportからの
新規child作成 — は必ず`audit`を再実行してください。rulesetとrepository設定はfileではなく
GitHub上のobjectなので、historyと一緒には移動しません。移動先はbranch rulesetが存在しない
状態になり、ローカルhookが通ったままGR-010・GR-011・GR-012のサーバ側強制が失われます。
identity変更を検出するのは`scripts/readme_ownership.py`で、その失敗メッセージがこの
コマンドを案内します。

`apply`の前に`plan`を確認してください。設定を変更するのは`apply`だけで、ローカルの
Administration権限と対象名の完全一致確認が必要です。各操作は再読込で検証されます。
policyはsquash-only mergeを必須化し、Discussionsとsquash commit messageの既定値は
repository overrideで選択できます。setup互換ラッパーは`gh`を直接呼びません。`DRY_RUN`は
`plan`、通常実行は完全一致する対象名を2回要求して`apply`へ委譲し、終了コードも引き継ぎます。

固定スクリプトからの移行では、引数なし形式は廃止され、CODEOWNERSなどの手動設定案内も
ラッパーからは出力されません。上記のとおり対象を明示し、このガイドをチェックリストとして
使用してください。

### 8. ローカルゲート導入 → エージェントに向ける

```bash
make setup                             # 依存導入 + pre-commit フック
```
Claude Codeは薄い`CLAUDE.md`アダプターを自動で読みます。他のエージェントには`AGENTS.md`を
読ませてください。アダプターは明示的なagent profileを検証し、記載された基盤・テンプレート・
プロジェクト入力を順番にすべて読み込みます。あとはissueを割り当てるだけです。

テンプレートには参照用の例モジュール（`src/modules/catalog/` ＋ `tests/modules/catalog/`）が
同梱されています。形を真似る（COD-050）か、実コードを書き始めるときに両方削除してください。
いつでも `make doctor` でテンプレートの自己チェック（frontmatter 整合性 + guard フックのテスト）が
できます。

---

## シナリオB — 基盤リポジトリ自体を別マシンにclone

```bash
git clone https://github.com/ea-Mitsuoka/ai-dev-foundation.git
cd ai-dev-foundation
# 素のテンプレートのルート Makefile は no-op なので、ここでは `make setup` は何もしません。
# git フックを直接入れます（pre-commit が必要 — 前提ツール参照）:
pre-commit install --hook-type pre-commit --hook-type pre-push
make doctor                            # テンプレートが壊れていないか検証
```
これは文字通り「cloneするだけ」ですが、各マシンで下記の**前提ツール**と**認証**は一度必要です。

### 保守対象fleetを監査

Foundation保守者は、明示的にremote refを更新した兄弟worktreeから、設定済みの全active継承関係を
検証できます。

```bash
make fleet-audit FLEET_WORKSPACE_ROOT=/path/to/worktrees
```

このコマンドはローカル、read-only、credential-freeであり、承認作業を作りません。正準fleet設定は
`active`、`paused`、`retired`を記録します。子のMakefileはこのtargetを継承しないため、
`ai-dev-foundation` worktreeから実行してください。worktree要件と結果の意味は
[固定fleetの監査](../../../.github/inheritance/README.md#audit-the-fixed-fleet)を参照してください。
ADR-0016により、private Template Syncを有効化した後もfleetの定期監査は無効のままです。

---

## マシンごとの前提ツール（両シナリオ共通）

新しいマシンで一度だけ導入:

| ツール | 用途 | 備考 |
|--------|------|------|
| `git`, `make` | 全般 | — |
| `gh`（GitHub CLI）| ガバナンス`plan`/`audit`/`apply`・互換setup・認証 | `gh auth login` |
| `pre-commit` | ローカルコミットゲート | `make setup`（プロファイル導入後）または `pre-commit install` |
| スタックのツールチェーン | build/test | uv(python) / pnpm+node(ts) / terraform(iac) |
| `gitleaks`, `trivy`, `syft` | ローカルの `make security-scan` / `sbom` | ローカルは任意。**CIは常時強制** |

スキャナはローカル任意です。GitHub Actions が全PRで実行するので、未導入でも「ローカルで結果が
見えない」だけです。

---

## 落とし穴（ぶつかる前に読む）

### push には `workflow` OAuth スコープが必要
`.github/workflows/` 配下を含む push はトークンの `workflow` スコープが必要です。
*"refusing to allow an OAuth App to create or update workflow ... without workflow scope"*
と拒否されたら:
```bash
gh auth refresh -h github.com -s workflow
```
これは**アカウント／マシンごと**の設定です。新環境ごとに一度実施する想定でいてください。

### ソロ開発 × ブランチ保護 ＝ 自分のPRをマージできない
`.github/governance/repository.json`の`required_approvals`をリポジトリ体制に合わせます。
第二のレビュアーなしで1件必須にすると自己マージできません。どちらか選択:

- **推奨（ガードレール維持）:** 共同開発者/レビュアーを1人追加、または AI レビュアー
  （[ai-review.yml](../../../.github/workflows/ai-review.yml)）を有効化。ただしAIのレビューコメントは
  GitHub上の *approval* にはならないため、真の自己マージには下の方法が必要。
- **ソロ実用:** repository policyで`"required_approvals": 0`に設定。
  これでも「ブランチ＋PR＋CI緑」（GR-010, GR-021）は保たれ、マージだけ自分で行えます。

`scripts/setup-github.sh`も同じrepository policyへ委譲するため、直接CLIと互換入口のどちらでも
設定したapproval件数が適用されます。

### 改行コード
`.gitattributes` がリポジトリ全体を LF 強制するので、Windows チェックアウトでもシェルフックと
Makefile は壊れません。グローバル `core.autocrlf=true` でこれと戦わないこと（`.gitattributes` が
対象ファイルでは勝ちますが、Git既定は素直にしておく）。

---

## 質問への回答

### Q. 別アカウントから「Use this template」してよい？ → **可能。1台のPCで完結できます**

テンプレートリポジトリにそのアカウントがアクセスできれば、どのアカウントからでも生成できます。

| テンプレートの公開設定 | 「Use this template」できるアカウント |
|------------------------|----------------------------------------|
| public | 誰でも（あなたの別アカウント含む）|
| private | 読み取り権限を持つアカウント（コラボレーター）／同じ Organization のメンバーのみ |

- 生成先のアカウント／Org はテンプレートのドロップダウンで選べます（テンプレート所有者と別でOK）。
- **結論:** このPC 1台で完結します。アカウントを切り替えて（または同一アカウントで）テンプレート
  → 新リポ生成 → clone → 開発、の流れで複数PCは不要です。
- visibilityは必要な機密性とgovernanceで決めます。認証を簡単にする目的でprivate repositoryを
  publicへ戻してはいけません。private親からの定期同期は、ADR-0016のread-only GitHub App方式を
  Issue #178で実装・承認してから有効化します。それまではローカルの継承操作を使います。

### Q. 全リポジトリを束ねる作業ディレクトリへの「グローバル指示」は仕組みとして想定されている？ → **はい（Claude Code の公式機能）**

Claude Code は起動時にディレクトリツリーを遡って `CLAUDE.md` を読み込みます。したがって階層で
グローバル指示を効かせられます（2026-07 時点の公式仕様で確認）:

| スコープ | 場所 | 適用範囲 |
|----------|------|----------|
| 組織管理ポリシー | Linux/WSL: `/etc/claude-code/CLAUDE.md` | マシン上の全セッション・全リポジトリ（個人設定で除外不可）|
| ユーザー | `~/.claude/CLAUDE.md` | あなたの全プロジェクト |
| **束ねる親ディレクトリ** | 例 `~/projects/CLAUDE.md` | **その配下の全リポジトリ**（cwd から親を遡って読む）|
| プロジェクト | `<repo>/CLAUDE.md` ＋ `.ai/` | そのリポジトリのみ（この基盤が提供）|

読み込み順は root 側 → cwd 側で、**cwd に近いものが後に読まれ優先**されやすい。すべて連結して
コンテキストに入ります（上書きではない）。

**推奨する構成:**
- 全リポ共通の「ハウスルール」→ `~/projects/CLAUDE.md`（例: 常に日本語で応答、あなたの名前・役割、
  優先ライブラリ、コミット文体）。**200行以内**に保つ。
- 真に全環境共通 → `~/.claude/CLAUDE.md`。
- 各リポの `.ai/` は**自己完結の正準ルール**のまま（100リポにコピーしても単独で機能し、
  ChatGPT/Gemini でも全ルールが読める）。

**重要な注意:**
- これは **Claude Code 固有**の仕組みです。ChatGPT/Gemini は親/グローバル `CLAUDE.md` を自動では
  読みません。ベンダー中立性のため、**ハードなガードレールは各リポの `.ai/` と PreToolUse フック**
  （この基盤の `guard-bash.sh` がまさにそれ）に置き、グローバル層は「競合しない補助的な好み」に
  留めてください。ハードルールをグローバル層“だけ”に置くと、他所へcloneした/他エージェントが読む
  リポジトリでそのルールが失われます。
- `CLAUDE.md` は「コンテキストであって強制設定ではない」（公式明記）。確実に**ブロック**したい操作は
  PreToolUse フックで実装します。

複数リポで共有したいルール断片は `.claude/rules/` にシンボリックリンクを張る方法も公式サポート
されています（例: `ln -s ~/shared-claude-rules .claude/rules/shared`）。

---

## クイックリファレンス:「別アカウントで clone だけで足りる？」

- **基盤を開発する**（シナリオB）: はい。`git clone`後にpre-commit hookを直接導入し、
  `make doctor`を実行します。workflow変更をpushするときは、そのマシンで`workflow` OAuth scopeも
  更新します。
- **新規プロジェクトを作る**（シナリオA）: いいえ。「Use this template」→ 上の初期化手順。
  cloneでは新規プロジェクトにこの基盤の履歴とプレースホルダが混入します。
