# Helm 3 Blockers

- Helm 2 vs Helm 3 releases
  - Helm 3 cannot manage releases that Helm 2 has created.
  - For Reckoner + Helm 3 to work, Helm 2 release configmaps must be migrated to Helm 3 secret objects.
    - This must be done manually, or by using the [Helm 2to3](https://github.com/helm/helm-2to3) plugin.
- 3 way merging
  - While this isn’t necessarily  a blocker, Helm 3 performs a three way merge operation when patching. Check this [PR](https://github.com/helm/helm/pull/6124) for more details
  - Some charts may be non-upgradeable depending on how they handle immutable fields
    - For example, the nginx-ingress chart fails to `upgrade` after being installed if some values are unset. See this [issue](https://github.com/helm/helm/issues/6378) for the details and workaround.
- No `--output json`
  - Check this [issue](https://github.com/helm/helm/issues/6437) for more details
  - This breaks the endtoend testing suite.
- Helm 3 does not create namespaces.
  - Workaround is to create the namespace in a `pre_install` hook.
  - Non-existent namespaces issue <https://github.com/FairwindsOps/reckoner/issues/75>
