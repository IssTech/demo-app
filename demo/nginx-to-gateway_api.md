# How To migrate from NGINX Ingress to Gateway API

## 1. Prerequisites
Install the Demo-App before continue this part, please read the [README.md](./../README.md) file

## 2. Modify the Demo-App Configuration
Go to the `nginx-demo` directory and apply the NGINX-Config to expose the app via your NGINX Ingress controller.

```
~/demo-app/demo/nginx-demo$ kubectl apply -f .
ingress.networking.k8s.io/demo-app-ingress created
service/demo-app-service configured
```

Modify your local `/etc/hosts` file to add a DNS record to the demo app and the IP do you get from `kubectl get node -o wide`

```
~/demo-app/demo/nginx-demo$ kubectl get node -o wide
NAME             STATUS   ROLES                  AGE     VERSION        INTERNAL-IP     EXTERNAL-IP   OS-IMAGE           KERNEL-VERSION     CONTAINER-RUNTIME
k8s-nginx-node   Ready    control-plane,master   3d23h   v1.33.6+k3s1   1.2.3.4         <none>        Ubuntu 24.04 LTS   6.8.0-39-generic   containerd://2.1.5-k3s1.33
```

Add the IP adress and the demo-app.local to your hosts file, and after that verify what port NGINX are listing on to expose the demo-app.

```
:~/demo-app/demo/nginx-demo$ kubectl get svc -n ingress-nginx
NAME                                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)                      AGE
ingress-nginx-controller             NodePort    10.43.70.146   <none>        80:30914/TCP,443:30196/TCP   3d23h
ingress-nginx-controller-admission   ClusterIP   10.43.28.227   <none>        443/TCP                      3d23h
```

Now let's run a web browser or curl to our demo app.

```
~/demo-app/demo/nginx-demo$ curl -I http://demo-app.local:30914/docs
HTTP/1.1 200 OK
Date: Mon, 01 Dec 2025 11:41:03 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 951
Connection: keep-alive
```





