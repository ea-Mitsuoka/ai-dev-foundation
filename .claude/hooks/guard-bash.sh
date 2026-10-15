#!/usr/bin/env bash
# PreToolUse hook: blocks Bash commands that would violate .ai/guardrails.md.
# Contract: reads hook JSON on stdin; exit 2 blocks the tool call and feeds stderr
# back to the agent; exit 0 allows. Keep patterns conservative — false blocks erode
# trust in the guard (agents must never be trained to bypass it — GR-012).

set -u

command_text="$(cat | { command -v jq >/dev/null 2>&1 && jq -r '.tool_input.command // empty' || cat; })"
[ -z "$command_text" ] && exit 0

block() {
  echo "BLOCKED by guardrail $1: $2 (see .ai/guardrails.md). Use the documented alternative instead of working around this guard." >&2
  exit 2
}

# GR-010: direct push to main/master (covers flags, "-u", and "HEAD:main" refspecs).
# Terminators include " so the guard still works when jq is absent and the raw hook
# JSON (…main") is grepped; "-" is NOT a terminator so feat/main-nav stays allowed.
# Only the push's own arguments are matched: [^&;|]* stops at the next command, so
# `git push origin feat/x && gh pr create --base main` is not a push to main.
echo "$command_text" | grep -Eq 'git +push\b[^&;|]*( |:)(main|master)( |"|$|&|;|\|)' \
  && block "GR-010" "direct push to main/master — open a PR from a branch"

# GR-011: force push (word-boundary safe: matches trailing -f/--force too, jq or not).
# Exception (LOG-0009): moving a floating tag (v1 -> v1.2.0) rewrites no branch history.
# Allowed only when the command's single `git push` targets refs/tags/ refspecs
# exclusively — the explicit form keeps a branch refspec from riding along, and the
# single-push requirement stops a second push smuggled behind && or ;. The tag charclass
# excludes separators so the refspec can't swallow a following command, and ":" so a
# src:dst refspec (refs/tags/v1:refs/heads/main would force-update main) never matches.
if echo "$command_text" | grep -Eq 'git +push\b.* (--force|-f)( |"|$)'; then
  tag_only='git +push +((--force|-f) +)?[A-Za-z0-9._-]+( +refs/tags/[^ "&;|:]+)+( +(--force|-f))? *("|$|;|&|\|)'
  push_count="$(echo "$command_text" | grep -oE 'git +push\b' | wc -l)"
  echo "$command_text" | grep -Eq "$tag_only" && [ "$push_count" -eq 1 ] \
    || block "GR-011" "force push — use --force-with-lease on your own PR branch only; a floating tag moves via 'git push --force <remote> refs/tags/<tag>' (tag refspecs only, one push per command)"
fi

# GR-012: bypassing hooks/CI
echo "$command_text" | grep -Eq -- '--no-verify|--no-gpg-sign|\[skip ci\]|\[ci skip\]' \
  && block "GR-012" "bypassing hooks or CI — fix the failing check instead"

# GR-031: destructive filesystem/database operations. Blocks recursive rm targeting any
# absolute/home path (/, /etc, ~, ~/x, $HOME...), quoted or not; workspace-relative
# (./x, bare names) is allowed. The leading [\'"]* also skips a JSON-escaped quote (\")
# so the guard still fires on the jq-absent raw-JSON path (LOG-0006).
echo "$command_text" | grep -Eq 'rm +-[a-zA-Z]*r[a-zA-Z]* +[\'\''"]*(/|~|\$HOME)' \
  && block "GR-031" "recursive delete of an absolute/home path — needs explicit human approval"
echo "$command_text" | grep -Eiq 'drop +(table|database|schema)' \
  && block "GR-031" "destructive database operation — needs explicit human approval"

# GR-032/GR-001: piping remote scripts into a shell (untrusted code exec / exfil vector).
# Also catches a privilege/env prefix after the pipe (| sudo sh, | env X=y bash).
echo "$command_text" | grep -Eq '(curl|wget)[^|;]*\|\s*(sudo\s+|env\s+[^|;]*)?(ba|z|da)?sh\b' \
  && block "GR-032" "piping a remote script into a shell — download, review, then run"

# git history rewrite on shared branches
echo "$command_text" | grep -Eq 'git +(rebase|reset +--hard) +[^ ]*origin/(main|master)|git +filter-(branch|repo)' \
  && block "GR-011" "history rewrite touching shared branches — needs explicit human approval"

# GR-003: reading a secret file's contents to stdout via a shell reader. The permission
# deny-list in .claude/settings.json only covers the Read tool; this covers the common
# Bash readers of the same secrets (`cat .env`, `grep x server.key`, `cat ~/.ssh/id_rsa`).
# The list is broad but not exhaustive — it is one layer of defence in depth alongside
# gitleaks and the container isolation, not a complete sandbox (LOG-0010). Safe templates
# (.env.example/.sample/.template) are intentionally NOT matched. The `(^|[^A-Za-z])`
# command anchor also matches the `"` that precedes the command on the jq-absent raw-JSON
# path, so the guard fires there too (LOG-0006); a start-of-line-only anchor would silently
# pass every command when jq is unavailable.
echo "$command_text" | grep -Eiq '(^|[^A-Za-z])(cat|less|more|head|tail|bat|nl|tac|rev|cut|sort|xxd|od|strings|base64|grep|egrep|fgrep|awk|gawk|sed) +[^|;&]*(\.env($|[^.A-Za-z])|\.env\.(local|prod|production|dev|development|staging|test|secret|secrets)([^A-Za-z]|$)|\.pem([^A-Za-z]|$)|\.key([^A-Za-z]|$)|\.p12|\.pfx|/\.ssh/|/\.gemini/|\.config/gcloud/)' \
  && block "GR-003" "reading a credential file to stdout — reference the variable/secret by name, never print its contents"

# GR-003: dumping the whole environment (may contain injected secrets) to stdout. Only the
# bare-dump form of printenv/env is blocked; the command-prefix form (`env FOO=1 cmd`) runs
# a program and stays allowed, as does naming one variable (`printenv PATH`). Same
# `(^|[^A-Za-z])` anchor as above so it also fires on the jq-absent raw-JSON path (LOG-0006).
echo "$command_text" | grep -Eq '(^|[^A-Za-z])(printenv|env) *("|$|;|&|\|)' \
  && block "GR-003" "dumping the environment can expose secrets — reference the specific variable name instead"

exit 0
