# **DEMO-APP: Data Sanitization Example**

This demo illustrates how to use Kasten by Veeam's "Backup-as-Code" capabilities to perform data sanitization (masking PII) during the restore phase. This is particularly useful when moving data between environments (e.g., from Production to Development) while ensuring sensitive information is protected.

This repository includes a file named backup-sanitization.yaml. This is a Kanister Blueprint. It instructs Kasten to:

1. **Backup:** Take a snapshot of the PostgreSQL volume.  
2. **Restore:** Spin up a temporary pod to execute SQL commands against the restored database.  
3. **Sanitize:** Run a SQL query that anonymizes the firstname of all users (replacing them with AAAAA-HASH-ID).

### **Run the Demo**

1. Register the Blueprint:  
   Apply the blueprint to your cluster so Kasten can see it.  
   ```
   kubectl apply -f demo/blueprint/backup-sanitization.yaml
   ```

2. **Create a Policy in Kasten:**  
   * Go to the Kasten Dashboard.  
   * Create a new Policy for the demo-app namespace.  
   * **Crucial Step:** Under "Advanced" or "Action Settings", assign the postgres-non-exclusive-backup blueprint to the Backup Action.  
3. **Run the Backup:**  
   * Execute the policy manually.  
   * Verify the backup completes successfully.  
4. **Restore & Sanitize:**  
   * Select the Restore point you just created.  
   * Choose to restore to a **new namespace** (e.g., demo-app-dev).  
   * Start the Restore.  
   * *Observation:* Kasten will restore the data, and then automatically run the Sanitization hook defined in the blueprint.  
5. **Verify Results:**  
   * Access the app in the new namespace (you may need to check the new NodePort or port-forward).  
   * Check GET /users/.  
   * You will see the user data exists, but all first names have been scrambled/sanitized.

---

## **dataSanitizationV2 (2026/11/20)**

A second action in the same blueprint, `postgres-non-exclusive-backup`. Use it
instead of `dataSanitization`. It needs **no special namespace**: it runs in
whatever namespace you restore into (`demo-app2`, `demo-restore`, ...). That
namespace needs what a restore of `demo-app` brings anyway: the Secret and the
Service `postgres-postgresql` and the database `demo_app_db`.

What V2 fixes:

| | `dataSanitization` | `dataSanitizationV2` |
|---|---|---|
| Waits for Postgres after the restore | no, `psql` fails if Postgres is still starting | yes, `pg_isready` up to 5 min |
| Session pod afterwards | left behind, so a second run in the same namespace fails | always deleted (`deferPhase`), also on failure |
| Image pull field | `pullPolicy` (not a Kubernetes field, ignored) | `imagePullPolicy` |
| SQL error | could go unnoticed | `ON_ERROR_STOP`, the hook fails |

The backup hooks (`backupPrehook`) now take the database host from the
StatefulSet's own `spec.serviceName` instead of a `kanister.io/serviceName`
label that the demo app never sets, so attaching the blueprint to a backup
works too. **Sanitization does not need the blueprint on the backup at all**:
it is a restore hook.

### Restore with sanitization, Kasten UI

Applications → demo-app → **Restore** → pick a restore point →
Application name e.g. `demo-app2` → (optional) transforms →
**Post-restore hook**: blueprint `postgres-non-exclusive-backup`, action
`dataSanitizationV2` → Restore.

### Restore with sanitization, CLI

```bash
kubectl apply -f demo/blueprint/backup-sanitization.yaml   # once
kubectl create namespace demo-app2                          # the action lives in the target namespace
cat <<'Y' | kubectl create --validate=false -f -
apiVersion: actions.kio.kasten.io/v1alpha1
kind: RestoreAction
metadata:
  generateName: restore-sanitized-
  namespace: demo-app2
spec:
  subject: {kind: RestorePoint, name: <restore point>, namespace: demo-app}
  targetNamespace: demo-app2
  hooks:
    onSuccess:
      blueprint: postgres-non-exclusive-backup
      actionName: dataSanitizationV2
Y
```

`--validate=false` because kubectl's client-side schema for Kasten's
aggregated API is incomplete; the server still validates. List restore
points with `kubectl -n demo-app get restorepoints.apps.kio.kasten.io`.

Check: `GET /users/` in the restored app shows first names like
`AAAAA-c4ca4-1`; the source in `demo-app` is unchanged.
