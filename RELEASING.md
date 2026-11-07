# Maintainer release policy

This document describes the release policy for this Insnrg fork. For official releases of this repository, maintainers must bump the integration version, create a matching Git tag, and publish a GitHub Release. These are maintainer requirements for this fork, not universal HACS requirements. HACS can use repositories without releases, and pushing to the default branch does not publish a release or automatically deploy it.

The shared workspace release guide is at `../../RELEASING.md` relative to this file. It is additional local guidance, not a dependency: this document keeps Insnrg's release instructions self-contained. That path points outside this Git repository and is not a portable link on GitHub or automatically distributed with the repository; follow this repository's instructions wherever the shared file is unavailable.

## Release checklist

1. Choose the next unique version for the release. Check the repository's current manifest and the remote tags/releases at release time; do not reuse an existing published version or assume the current checkout is already released.
2. Update `custom_components/insnrg/manifest.json`'s `version` to that version. Update release notes or a changelog if one is maintained; do not assume a changelog exists.
3. Run the available tests (`python -m pytest -q`) and review `git status` and the diff. Do not skip, weaken, or misrepresent tests. The repository's HACS and hassfest GitHub Actions workflows validate pushes and pull requests; they are not a substitute for the test command.
4. Commit the intended changes and push them to the explicitly approved branch. Do not commit directly to `main` by default. Confirm the intended branch and commit with the repository owner before release; publishing a release requires separate authorization. Never force-push or move/retag an already published release tag.
5. Review relevant GitHub Actions results when available and report their actual status accurately. These workflows are useful supplementary checks, not a release gate for this project; absence of a run is not a pass. The available project tests and required behavior checks must pass. Do not describe failed, pending, or unrun automation as successful.
6. Create an annotated tag named `v<version>` on the exact intended release commit, then push that tag to the correct `origin`. For example, after substituting the actual version and commit (these are illustrative commands, not actions to run as-is):

   ```sh
   git tag -a v<version> <release-commit> -m "Release <version>"
   git push origin v<version>
   ```

7. Publish a non-draft GitHub Release for that exact tag with concise, accurate, feature-focused release notes. For example, with the actual values substituted:

   ```sh
   gh release create v<version> --title "v<version>" --notes-file <release-notes-file>
   ```

   The GitHub UI may be used instead. Confirm the release points to the intended tag and commit; creating the tag alone is not the same as publishing the release.
8. Verify on GitHub that the tag and published release exist, the release commit contains the matching manifest version, and HACS reports the released version where that can be checked. Clearly report unknown or unavailable HACS detection. Users should follow Home Assistant's guidance to reload the integration or restart Home Assistant as appropriate. Report any end-to-end installation or runtime verification as unverified unless it was actually performed.

## Manual release procedure

When a workflow supports manual dispatch and an additional check is useful, an authorized maintainer may run it, for example `gh workflow run <workflow-file> --repo <owner>/<repo> --ref <branch>`. Confirm the remote branch still points to the reviewed candidate commit before dispatching, then verify the run's head SHA, status, conclusion, and URL. Do not change repository Actions settings or workflow files as part of release preparation.

The manual release steps (review, available project tests, versioned commit, annotated tag, published non-draft release, and post-release verification) remain mandatory. Document material check limitations honestly in the maintainer handoff; release notes should describe the release itself and must not claim verification that was not performed. Deployment and live operational checks always remain separate and require their own authorization.

## Deployment is separate

Publishing a GitHub Release does not run or authorize deployment. Deployment and any live operational checks require separate permission. The repository's local Docker deployment script stops/restarts services, replaces the target, deletes a log, and has no rollback; do not run it blindly as part of a release. Review its effects and obtain explicit authorization before any deployment.
