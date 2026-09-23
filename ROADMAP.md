# Improvement ideas

The local vault, autosave, backups, cache recovery, and concurrent edit protection are implemented in v9. The suggestions below are future work, ordered by likely value.

## Next: reliability and control

1. Add a visible save history with timestamps, backup sizes, and one-click preview/restore.
2. Show a field-by-field conflict diff and allow a careful merge across tabs.
3. Add undo/redo for edits, deletes, imports, and bulk JSON changes.
4. Add a recycle bin and delayed permanent deletion.
5. Check vault schema and reference integrity on every import, with a dry-run preview.
6. Detect duplicate projects and near-duplicate URLs before import.
7. Keep import reports listing new, updated, skipped, and conflicting records.
8. Add a health screen: current vault, last successful save, storage free space, backup count, and schema version.
9. Add checksums and a restore drill for backups.
10. Make vault schema migrations explicit and reversible.

## Organizing and finding links

11. Search across all dashboards, including descriptions, tags, and notes.
12. Add saved searches and named views for common workflows.
13. Provide keyboard shortcuts and a command palette.
14. Add recent and frequently opened links, stored locally.
15. Add pinned items, per-dashboard ordering, and drag-and-drop categories.
16. Add multi-select actions to move, retag, star, archive, or delete records.
17. Add tags with autocomplete, rename, and cleanup tools.
18. Add link health checks with opt-in network validation and a last-checked timestamp.
19. Highlight malformed URLs and local file bookmarks with clear actions.
20. Provide a dedicated local-path type, with an optional user-confirmed desktop opener.
21. Add a compact view, larger cards, and configurable visible fields.
22. Add a print-friendly view and an exportable inventory report.

## Data and integrations

23. Support multiple named vaults/profiles selected from a configured folder.
24. Add import/export adapters for browser bookmarks, CSV, Markdown, and HTML bookmarks.
25. Offer targeted export by dashboard, category, tag, or selection.
26. Add optional link metadata fetching (title and favicon) with user-controlled access.
27. Add templates for TestSavvy, Jira, Confluence, Google Drive, and common project workspaces.
28. Add project relationships: application, environment, documentation, repository, tickets, and owner.
29. Add a local, read-only API for other tools to query links by tag or ID.
30. Add a bulk URL replacement tool for server/domain migrations.

## Platform and security

31. Package a signed desktop installer and tray launcher so Python need not be installed separately.
32. Offer optional encrypted vaults with a user-managed passphrase and documented recovery limits.
33. Add an idle lock if sensitive notes are eventually stored.
34. Add an optional sync adapter for a user-selected approved location, with explicit conflict resolution.
35. Add versioned settings and a guided settings page for changing directories safely.
36. Add accessibility checks, screen-reader labels, and full keyboard navigation.
37. Add automated browser tests for Chrome, Edge, and Firefox on Windows.

**Suggested next milestone:** restore/history UI, import validation preview, duplicate detection, and a dedicated local-path link type.
