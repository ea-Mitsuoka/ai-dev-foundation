# Discussion Categories

GitHub does not support configuring Discussion categories as code — apply this list
manually in **Settings → Features → Discussions → Categories** when instantiating.

| Category | Format | Purpose |
| -- | -- | -- |
| Announcements | Announcement (maintainers post) | Releases, breaking changes, policy updates |
| Ideas | Open discussion | Early-stage proposals before they become issues/ADRs |
| Q&A | Question/Answer | Usage and development questions; answered = knowledge base |
| Show & Tell | Open discussion | Things built with/on the project |
| Design Reviews | Open discussion | Pre-ADR design debate; outcome graduates to `docs/adr/` |
| Agent Reports | Open discussion | AI agents post retrospectives / recurring friction they hit (feeds rule improvements in `.ai/`) |

Routing rule: question → Q&A; concrete actionable work → Issue; decision with long-term
consequences → Design Reviews, then ADR. Vulnerabilities never go to Discussions
(SECURITY.md).
