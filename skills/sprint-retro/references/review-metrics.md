# Review-workload counting contract

## Windows, identity, and records

Record the exact start and inclusive cutoff in local time and UTC. Use GitHub
timestamps, not search update dates, to qualify activity. For a running update,
the incremental window is **strictly after the previous cutoff through the new
cutoff inclusive**. Keep original ledgers/snapshots unchanged.

Discover candidates through author, reviewed-by, commenter, mention/involvement,
and journal seeds; searches alone are not event counts. Check pagination and
search completeness. If a result cap is reached, split discovery or qualify
coverage. For an incremental refresh, prioritize newly discovered candidates
and previously known PRs with later updates; do not rescan unrelated commits.

Use account identity and PR author to split other-authored and own-authored
activity. Count:

| Metric | Qualification and deduplication |
| --- | --- |
| Review submissions | User's submitted review records with non-null `submitted_at` in the window, once per review ID. Include empty-body submissions; exclude pending drafts. |
| PRs with submitted reviews | Unique `(repository, PR number)` among qualifying submitted reviews. |
| Inline comments | User's PR review comments, including replies, qualified by creation time and deduplicated by comment ID. |
| PR-conversation comments | User's issue-conversation comments on PRs, counted separately by creation time and ID. |
| PRs with review/comment activity | Union of those event types by PR. If this exceeds PRs with submitted reviews, label the comment-only PRs rather than implying formal reviews. |

Review bodies are not additional comments. Use typed event keys so IDs in
different endpoint namespaces cannot collide. Later merges, PR openings, edited
timestamps and requested-reviewer status do not create review submissions.
Approval/change-request/comment breakdowns reflect retrieved review records;
do not reconstruct unavailable historical states from current labels.

Report colleague activity as the headline, own activity separately, and combined
totals only with an explicit label. A submission is not necessarily a complete
review pass. Codex-assisted posts under the user's account count as that
account's records with attribution, not proof of personally typed text or hours.
Missing/deleted/private events and unposted reviews remain outside the measured
universe.

## Reviewed-PR diff volume

Use **additions + deletions**, counted **once per qualifying PR**, as a
**reviewed-PR snapshot diff-volume proxy**. Default to PRs with submitted reviews;
report any broader comment-only volume separately. Own-authored PR volume stays
out of the colleague headline.

For each included PR, save the snapshot head/base identifiers and diff totals;
check additions, deletions and file count against the complete files endpoint.
Disclose file-list/API limits or missing data rather than inventing a complete
per-file audit. Record review commit IDs versus the snapshot head; matching
heads still do not prove that the base or full diff matches review-time history.

Include tests, documentation, data, configuration, generated content, and renames
unless a separately defined filter is requested. Identify material large-file
churn. PR-file entries and distinct repository/path pairs are different counts;
overlapping changes across PRs are not globally unique lines.

Never call the proxy exact lines read, unique source lines, historical diff
reconstruction, reviewed hours, or review-pass-weighted effort.

## Additive updates

1. Preserve baseline event IDs, included PR keys and their original diff
   snapshots. Reconcile new event IDs against both old and new ledgers.
2. Add every qualifying new review event, even if it is on an already counted
   PR. Report the number of re-reviewed PRs separately from new unique PRs.
3. Add full diff volume only for PRs absent from the prior included-PR set that
   now qualify. Multiple new reviews of one PR add its snapshot once.
4. For an old PR with a new revision/re-review, do not add its entire diff again
   or silently replace the original snapshot. State that newly changed lines
   on that PR are not independently measured by this additive proxy.
5. Show baseline + interval additions = running event totals, and baseline
   volume + new unique-PR volume = running snapshot volume. The running line
   total combines snapshots taken at different times; label that limitation.

For example, if a baseline includes PR A and a later interval contains two
re-reviews of A and one review of new PR B, add **three review events, one unique
PR, and B's diff volume once**. Do not add A's full diff twice.

If the user instead requests refreshed current snapshots or review-time diff
reconstruction, treat that as a different metric with a new label and scope;
do not present its difference as the ordinary additive running total.

## Durable evidence and checks

Alongside `GitHub.md`, retain compact machine-readable metrics and ledgers when
counts will be refreshed. Their format may fit the task, but preserve:

- Window/cutoffs, account, scope/definition, discovery queries and visibility
  limits, baseline lineage, and the timestamp of snapshot retrieval.
- Typed event key, PR key/author, actor, timestamp, review state/commit where
  applicable, and source pointer.
- PR key, own/other classification, snapshot identifiers, additions, deletions,
  file count, inclusion reason, and source pointer.

Raw provider bodies can remain in per-run scratch; future updates must not
depend solely on a temporary directory remaining available. Keep credentials
and unrelated personal content out of retained ledgers.

Recompute counts from event IDs, union PR sets instead of summing overlapping
sets, and check additive line arithmetic. An independent quantitative check
should use cached records/ledgers, not merely repeat the summary's numbers.
Missing baseline records mean the update cannot be proved deduplicated: report
that gap and recover only the needed evidence before claiming a running total.
