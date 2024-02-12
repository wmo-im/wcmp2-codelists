# GitHub Actions

The following GitHub Actions are in place for this repository:

- on Pull Request: test the generation of WCMP2 Codelists to TTL files
- on Commit/Push to `main` branch: generate WCMP2 Codelists to TTL files, and push to `publication` branch
- on Commit/Push to `publication` branch: publish the TTL files to the WMO Codes Registry testing environment

Edit `codelists/*.csv` files -> GitHub Pull Request (test generation) -> Merge Pull Request (generate and commit to `publication` branch) -> Publish to WMO Codes Registry testing environment

Publication to the WMO Codes Registry operational environment is executed as a manual step.
