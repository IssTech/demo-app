# Backup by label: `backup=daily-3version`

A Kasten policy that does not list namespaces by name. Instead it backs up
**every namespace that carries the label `backup=daily-3version`**. To protect an
app you label its namespace; to stop, you remove the label. Nobody edits the
policy.

| | |
|---|---|
| Policy | `backup-daily-3version` in `kasten-io` ([policy.yaml](policy.yaml)) |
| Selects | namespaces labelled `backup=daily-3version` |
| Schedule | daily (`@daily`) |
| Kept | 3 local restore points, and 3 exported to the location profile `safespring` |

## Try it with the demo app

```bash
# 1. The policy (once per cluster)
kubectl apply -f demo/kasten-label-backup/policy.yaml

# 2. Put the demo app under it
kubectl label namespace demo-app backup=daily-3version

# 3. Run it now instead of waiting for the daily run
cat <<'Y' | kubectl create -f -
apiVersion: actions.kio.kasten.io/v1alpha1
kind: RunAction
metadata:
  generateName: run-backup-daily-3version-
  namespace: kasten-io
spec:
  subject: {kind: Policy, name: backup-daily-3version, namespace: kasten-io}
Y

# 4. Follow it: Kasten -> Dashboard -> Actions, or
kubectl -n demo-app get restorepoints.apps.kio.kasten.io
```

Restore from the Kasten UI: **Applications → demo-app → Restore**, pick a
restore point. To restore under a new name and URL, see
[`../transformsets`](../transformsets).

## Take an app out again

```bash
kubectl label namespace demo-app backup-
```

New runs skip it from then on. Restore points already taken stay until their
retention (3 days) runs out.

## Notes

- The label must be on the **namespace**, not on a Deployment.
- With another policy that also names the same namespace, the app is backed up
  twice. Use one or the other.
- Kasten writes the export's `migrationToken`/`receiveString` into the live
  policy itself. Do not commit them back; patch the field you mean instead of
  re-applying the file.
