# **DEMO-APP: FastAPI & PostgreSQL on Kubernetes**

This is a Demo Application built with **FastAPI** and **PostgreSQL**, designed specifically for use with **Kasten by Veeam**. Its primary purpose is to demonstrate Kubernetes Backup and Restore capabilities, specifically highlighting **"Backup-as-Code"**.

It includes a Multiple Kanister Blueprint that shows multiple demo senarios, the first was performing **Data Sanitization** (masking PII) during the restore phase, showing how you can transform data securely when moving between environments (e.g., from Production to Development).

## **1\. Architecture**

* **App:** FastAPI (Python) web server.  
* **Database:** PostgreSQL 17 (deployed as a StatefulSet).  
* **Infrastructure:** Kubernetes Namespace, ConfigMaps, Secrets, and Services.

## **2\. Prerequisites**

* A running Kubernetes Cluster (Single node clusters like K3s, Minikube, or Docker Desktop work fine).  
* kubectl installed and configured.  
* **Veeam Kasten** (for the backup/restore demo).

## **3\. Installation**

You can deploy the entire stack (Namespace, Postgres, and the FastAPI app) using the included manifest file.

### **Step 1: Deploy**

Run the following command to apply the Kubernetes manifests:

```
kubectl apply -f install-demo-app.yaml
```

### **Step 2: Verify**

Check that the pods are running in the demo-app namespace:

```
kubectl get pods \-n demo-app
```

*Wait until all pods show a status of Running.*

### **Step 3: Access the Application**

The application Service is exposed via NodePort on port **30080**.

* `kubectl get node -o wide` to find your NODE-IP.
* **Remote Cluster:** http://\<NODE-IP\>:30080

## **4\. Usage & Testing (CRUD Operations)**

The application includes an interactive Swagger UI to manage the data.

1. **Open the Docs:** Navigate to `http://127.0.0.1:30080/docs` in your browser.  
2. **Populate the Database (Seeder):**  
   * Find the POST /populate\_50 endpoint.  
   * Click **Try it out** \-\> **Execute**.  
   * *Result:* 50 synthetic users are added to the database.  
3. **Read Data:**  
   * Use the GET /users/ endpoint to see the list of created users.  
4. **Modify/Delete:**  
   * Use PUT or DELETE on /users/{user\_id} to modify specific records.

## **5\. Install Veeam Kasten**

To be able to install Veeam Kasten and use it with this demo app, either you install it via the Kasten Helm chart or Openshift Operator.
You have a detailed guide on how to do this in the following blog post:

👉 [**Get Started with Protecting Your Containers**](https://www.isstech.io/blogg/get-started-with-protecting-your-containers)

## **6\. More senarios**
1. [Migrate from NGINX to Traefik Example](./demo/nginx-treafik.md)
2. [Sanitize Data on Restore Example](./demo/data-sanitization.md)

## **7\. Known Issues & Storage**

If your environment is a small K3s or local cluster, you might be using the local-path Storage Class:

$ kubectl get sc  
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE        
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   

**Recommendation:** While Kasten supports Generic Storage Backup (GCB) for these environments using sidecars, for a production-grade experience, it is highly recommended to run a true **CSI (Container Storage Interface) Volume Snapshot** capable storage class, such as:

* Ceph / Rook  
* Longhorn  
* AWS EBS / Azure Disk / Google PD  
* NetApp / Pure Storage