# Step 12.4: Minikube Kubernetes Manifests & Learning Setup Report

## 1. Objective & Business Relevance
Step 12.4 creates standard declarative Kubernetes manifests (`deployment/k8s/sentinel_app.yaml`) targeting local Minikube or managed cloud Kubernetes clusters (EKS/GKE). In enterprise institutional surveillance, containerized workloads require declarative pod scaling, self-healing liveness probes, namespace isolation, and strict compute quotas.

## 2. Technical Explanation & Architectural Fit
- **Kubernetes Architecture (`deployment/k8s/sentinel_app.yaml`)**:
  - `Namespace`: Dedicated `market-sentinel` namespace isolating application objects.
  - `sentinel-backend`: Deployment with explicit CPU and memory resource requests/limits (`requests: 512Mi / 250m`, `limits: 1536Mi / 1000m`), HTTP liveness probe on `/health`, readiness probe on `/ready`, and internal `ClusterIP` service.
  - `sentinel-frontend`: Deployment with `NodePort` service mapping port 30080 for direct host browser access on Minikube.

## 3. Technology Decisions & Alternatives Considered
- **Standard Kubernetes Manifests vs Helm**:
  - Pure declarative YAML manifests provide transparent learning and deployment across developer Minikube nodes without requiring Helm templating engine dependencies.

## 4. Files Created / Modified
- `deployment/k8s/sentinel_app.yaml`: Kubernetes Namespace, Deployment, and Service definitions.
- `tests/unit/test_k8s_manifests.py`: Automated tests validating resource limits and probe specifications.
- `docs/step_reports/phase_12_step_04_k8s_manifests.md`: This report.

## 5. Commands Executed & Testing Report
```bash
python -m pytest tests/unit/test_k8s_manifests.py -v
```
Output:
```
tests/unit/test_k8s_manifests.py::test_k8s_manifests_structure PASSED    [100%]
============================== 1 passed in 0.12s ==============================
```

## 6. Known Limitations & Edge Cases
- When running in local Minikube, run `minikube service sentinel-frontend-service -n market-sentinel` to open the ingress tunnel.

## 7. Status & Sign-off
- **Status**: COMPLETED & VERIFIED
- **Phase 12 Step**: Step 12.4 Approved
