# demo.int.isstech.io: IssTech's own install of the demo app

The demo app on IssTech's Kubernetes cluster, public at
**https://demo.int.isstech.io**, backed up by Kasten, and restorable as a
second copy on **https://demo2.int.isstech.io** with a TransformSet.

| File | What it is |
|---|---|
| `kustomization.yaml` | The base install (`../k8s-base-install`) plus: no committed DB password, Ollama pinned (never `:latest`) with 20 GiB for models, resource limits |
| `gateway.yaml` | Certificate (Let's Encrypt), ReferenceGrant and the HTTPS + HTTP-redirect routes on the shared Gateway `cilium-gateway` (namespace `isscontrol`) |
| `kasten/policy.yaml` | `demo-app-protection`: daily backup of `demo-app`, exported to the Safespring profile. The Ollama model cache is excluded |
| `kasten/transformset-demo2.yaml` | `demo2-int-isstech-io`: a restore into `demo-app2` answers on demo2 |

The Gateway listeners (`demo-*`, `demo2-*`) live in IssTech/IssControl,
`k8s/cluster/shared-gateway.yaml`. The owner script that installs
everything is `IssAssist.main/handoff/owner-demo-app-2026-11-20.sh`.

## Restore to demo2

Kasten → Applications → `demo-app` → **Restore** → pick a restore point →
**Application name: `demo-app2`** (a new namespace) → **Apply transforms** →
`demo2-int-isstech-io` → **Restore**. cert-manager issues the demo2
certificate within a minute or two; the original on demo keeps running.

Remove the copy with `kubectl delete namespace demo-app2`.

## Open to everyone

By the owner's decision (2026/11/20) the app has no login. Anyone can open
the Swagger UI, add or delete demo users and use the AI chat (which runs
`llama3.2:3b` on CPU). The data is synthetic. Limits on CPU and memory
keep the chat from starving the cluster.
