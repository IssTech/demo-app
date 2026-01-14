# **Migration Scenarios: Surviving the Ingress Jungle**

This demo shows how to use Kasten by Veeam's "Backup-as-Code" capabilities to migrate an application from using the NGINX Ingress Controller to Traefik. This is particularly useful given the deprecation of NGINX in favor of more modern ingress solutions.

As Kubernetes evolves, you might need to migrate from legacy NGINX Ingress to modern alternatives like **Traefik** or the **Gateway API**. Kasten makes this "Backup-as-Code" easy.

For a deep dive, read the full blog post:  
👉 (The Ingress Jungle: Surviving the NGINX Deprecation with Backup-as-Code)[https://www.isstech.io/blogg/the-ingress-jungle-surviving-the-nginx-deprecation-with-backup-as-code]

## **Scenario A: Migrate from NGINX to Traefik (Using Transform Sets)**

If moving to Traefik, we can preserve the Ingress resource but must transform it during restore to match the new controller.

1. Create the Transform Set:  
   Apply the treafik-transformSet.yaml file. This tells Kasten to change the ingressClassName from nginx to traefik and remove NGINX-specific annotations.  
   ```
   kubectl apply -f treafik-transformSet.yaml
   ```

2. **Restore with Transform:**  
   * In Kasten, start a Restore.  
   * Select the **"Transforms"** option.  
   * Choose the migrate-nginx-to-traefik transform set.  
   * Restore\! The application comes up pre-configured for Traefik.

## **Scenario B: Migrate from NGINX to Gateway API (Using Exclusions)**

Gateway API uses different resources (Gateway, HTTPRoute) than the standard Ingress. We cannot simply "transform" an Ingress into a Gateway.

1. **Restore with Exclusion:**  
   * In Kasten, start a Restore.  
   * Select **"Exclude Resources"**.  
   * **Exclude** the Ingress resource (we don't want the old NGINX config).  
   * Restore the application.  
2. **Apply Gateway API Config:**  
   * Once restored, apply the new Gateway API definitions (e.g., for Cilium or other providers):

```
kubectl apply -f gateway-cilium.yaml
```
*Note: This file deploys the GatewayClass, Gateway, and HTTPRoute required to expose the app.*
