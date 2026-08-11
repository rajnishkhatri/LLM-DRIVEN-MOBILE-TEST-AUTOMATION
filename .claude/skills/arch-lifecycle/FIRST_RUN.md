# arch-* family — first run

If `.arch/binding.toml` does not exist when any arch-* skill is invoked:

1. Inspect the workspace: is `cases/ArchitectureBook` (or an equivalent
   methodology bundle) present? Is there an existing constitution/rules file?
2. Propose a binding from `binding.template.toml`, adapted to what was found.
3. Human confirms (or edits) each key.
4. Persist to `.arch/binding.toml` with a `# confirmed <date>` header and
   create the four artifact-home directories.

Never silently invent a binding: the artifact homes decide where kata output
accumulates, and the methodology source decides what the skills cite.

Sibling arch-* skills do not carry their own binding files — they resolve
through this skill's schema. If a sibling is invoked standalone in a workspace
with no binding, run this first-run flow before its stage work.
