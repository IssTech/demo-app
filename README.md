# DEMO-APP based on FastAPI and PostgreSQL

This is a Demo-App that are used for Kasten by Veeam to demostrate how to Backup and Restore a App running in Kubernetes.

It is including a blueprint that shows the power of `Backup-as-Code` so you can even modify the database content during the restore phase that is called `Sanitazing`.

## 1. Prerequisites

Running Kubernetes Cluster, single node cluster is good enough for this app to run on.

## 2. Installation

Either you clone the project and run `kubectl apply -f ./demo/k8s-base-installation/install-demo-app.yaml` or you can run direct from our GitHub repository. 



The server will start running, typically at `http://127.0.0.1:8000`.

## 6. Testing the API (CRUD Operations)

You can test all the functionality directly in your browser using the interactive documentation provided by FastAPI (Swagger UI).

Open the Docs: Go to `http://127.0.0.1:8000/docs` in your web browser.

Populate the Database (C - Seeder):

Find the POST `/populate_50` endpoint.

Click "Try it out" and then "Execute".

You should receive a 201 status code and a message confirming 50 users were added. This data is now persistent inside your Docker volume.

Read All Data (R):

Find the GET `/users/` endpoint.

Click "Try it out" and then "Execute".

The response body will show a JSON list of all 50 generated users, confirming your connection to the Dockerized database works.

Create a Single User (C):

Find the POST `/users/` endpoint.

Click "Try it out" and replace the example body with your custom data:
```
{
  "firstname": "John",
  "lastname": "Doe",
  "zip_code": "10001",
  "country": "USA"
}
```

Execute. Note the id of the newly created user (e.g., 51).

Modify a User (U):

Find the PUT `/users/{user_id}` endpoint.

Click "Try it out", enter the id from step 4 (e.g., 51) in the path parameter, and update the body:
```
{
  "firstname": "Jane",
  "lastname": "Doe",
  "zip_code": "90210",
  "country": "USA"
}
```

Execute and verify the user data is updated.

Remove a User (D):

Find the DELETE `/users/{user_id}` endpoint.

Click "Try it out", enter the id (e.g., 51), and execute.

The status code should be 204 No Content. Verify by trying to GET `/users/51` which should return a 404 Not Found.

## Known Issues

If your environment is a small SuSE k3s or Ubuntu SnapK8s you probably ending up with local-path Storage Class. 
```
$ kubectl get sc
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  3d21h
$ 
```

Kasten has a legacy support that calles **Generic Storage Backup (GCB)** that can startup a Kanister Sidecar, but this is not recommended so you should run a true **Container Storage Interface (CSI) Volume Snapshot** storage class like Ceph, QuoByte, NFS, Longhorn, IBM Storage Scale and many other. 