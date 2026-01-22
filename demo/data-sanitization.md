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
   kubectl apply -f backup-sanitization.yaml
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