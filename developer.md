# Release a new version of the software

## PyPi

For a step-by-step video guide check out the [release video](https://www.youtube.com/watch?v=tsAWDumpcW8)

1. Check that the publishing action creating the wheels and source distribution appear correctly.
2. Go to Actions tab and workflow "Bump version".
3. Run the workflow manually by clicking the "Run workflow" button and adjusting the parameters.
    - Set version bump level (i.e. "patch")
    - Set new version "X.Y.Z" w/o "v" prefix
    - Disable dry run, after you are confident that the workflow is working correctly (i.e. running dry run once).
4. Optionally, check the publishing action again for the new version.
5. Manually, run the publishing action by clicking the "Run workflow" button in order to publish to Test-PyPi.
6. Optionally, inspect the URL returned after Test-PyPi uploading to check the package.
   Check that sdist and wheel are available for the new version.
7. Go to the Releases page.
   Select "Draft a new release".
8. Pick the tag created by the "Bump version" workflow (here with a "v" prefix) and click "Generate release notes".
   Tick "Set as the latest release" if this is the latest release and "Create a discussion" in the Category "Announcements".
9. Click "Publish release".
10. A build and publish to (Test)-PyPi workflow will be triggered automatically it should again upload sdist and wheel to PyPi.

## Conda
