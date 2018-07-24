## Kubernetes Dashboard

```
  kubernetes-dashboard:
    version: "0.6.3"
    values:
      resources.requests.cpu: 250m
      resources.requests.memory: 300Mi
      resources.limits.cpu: 250m
      resources.limits.memory: 300Mi
```

## Cluster autoscaler

```
  cluster-autoscaler:
    repository: stable
    version: "0.7.0"
    values:
      cloudProvider: aws
      replicaCount: 2
      autoscalingGroups[0].name: nodes-us-east-1a.production-1.kube.example.com
      autoscalingGroups[0].maxSize: "15"
      autoscalingGroups[0].minSize: "3"
      autoscalingGroups[1].name: nodes-us-east-1c.production-1.kube.example.com
      autoscalingGroups[1].maxSize: "15"
      autoscalingGroups[1].minSize: "3"
      autoscalingGroups[2].name: nodes-us-east-1d.production-1.kube.exapmle.com
      autoscalingGroups[2].maxSize: "15"
      autoscalingGroups[2].minSize: "3"
      awsRegion: us-east-1
      resources.requests.cpu: 100m
      resources.requests.memory: 300Mi
      resources.limits.cpu: 100m
      resources.limits.memory: 300Mi
      rbac.create: "true"
      image.pullPolicy: Always
      tolerations[0].key: node-role.kubernetes.io/master
      tolerations[0].effect: NoSchedule
      extraArgs.v: "2"
      extraArgs.logtostderr: ""
      extraArgs.balance-similar-node-groups: ""
      extraArgs.skip-nodes-with-system-pods\=false: ""
      extraArgs.scan-interval: "30s"
      extraArgs.expander: "most-pods"
```

## Heapster

```
  heapster:
    version: "0.2.10"
    values:
      rbac.create: "true"
      resources.requests.cpu: 100m
      resources.requests.memory: 300Mi
      resources.limits.cpu: 100m
      resources.limits.memory: 300Mi
```

## Datadog

```
  datadog:
    version: "0.11.3"
    repository: stable
    values:
      datadog.apiKey: "${DATADOG_API_KEY}"
      daemonset.updateStrategy: RollingUpdate
      daemonset.tolerations[0].key: node-role.kubernetes.io/master
      daemonset.tolerations[0].effect: NoSchedule
      resources.requests.cpu: 100m
      resources.requests.memory: 250Mi
      resources.limits.cpu: 200m
      resources.limits.memory: 500Mi
      kube-state-metrics.rbac.create: "true"
      rbac.create: "true"
      kubeStateMetrics.enabled: "true"
      datadog.leaderElection: "true"
```

## spotify-docker-gc

```
  spotify-docker-gc:
    version: "0.1.3"
```

## external-dns

```
  external-dns:
    version: "0.6.1"
    values:
      registry: noop
      resources.requests.cpu: 10m
      resources.requests.memory: 50Mi
      domainFilters[0]: "example.com"
      rbac.create: "true"
      provider: aws
      rbac.create: "true"
      registry: "noop"
```

## rbac-manager

```
rbac-manager:
  repository:
    git: https://github.com/reactiveops/rbac-manager.git
  chart: chart
  version: master
  namespace: rbac-manager
  values:
    rbacDefinition:
      enabled: true
      content:
        rbacUsers:
        - user: user@example.com
          kind: ServiceAccount
          clusterRoleBindings:
            - clusterRole: cluster-admin
```

## nginx-ingress (TLS termination in nginx)

```
  nginx-ingress-public:
    chart: nginx-ingress
    namespace: infra
    values:
      controller.replicaCount: 3
      controller.minAvailable: 2
      defaultBackend.replicaCount: 2
      defaultBackend.minAvailable: 1
      controller.ingressClass: "nginx-ingress-public"
      controller.service.externalTrafficPolicy: "Local"
      controller.publishService.enabled: "true"
      controller.resources:
        requests.cpu: 100m
        requests.memory: 200Mi
        limits.cpu: 200m
        limits.memory: 400Mi
      rbac.create: true
      controller.podLabels.nginx-affinity: nginx-ingress-public
      controller.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].key: nginx-affinity
      controller.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].operator: In
      controller.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].values[0]: nginx-ingress-public
      controller.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].topologyKey: "kubernetes.io/hostname"
```

To do http TLS termination on the ELB add

```
    values:
      controller.service.annotations.service\.beta\.kubernetes\.io\/aws-load-balancer-ssl-cert: "arn:aws:acm:us-east-1:111111111111:certificate/b4e0476f-7caa-4c3b-b927-b4e0476f1111"
      controller.service.annotations.service\.beta\.kubernetes\.io\/aws-load-balancer-backend-protocol: http
      controller.service.targetPorts.https: 80
      controller.service.targetPorts.http: 80
    values-strings:
      controller.service.annotations.service\.beta\.kubernetes\.io\/aws-load-balancer-ssl-ports: 443
```


## newrelic

```
  newrelic-infrastructure:
    # Upstream doesn't work with 1.8 because it uses apps/v1 (https://github.com/kubernetes/charts/pull/5557)
    repository:
      git: git@github.com:reactiveops/charts.git
      path: stable
    version: "newrelic-1.8"
    # version: 0.3.0
    values:
      config.custom_attributes.APP: "example.com"
      config.custom_attributes.DATACENTER: "aws"
      config.custom_attributes.DOMAIN_NAME: "prod.example.com"
      config.custom_attributes.HOST_TYPE: "webapp"
      config.custom_attributes.REGION: "us-east-1"
      config.custom_attributes.STAGE: "production"
      cluster: "prod.example.com"
      licenseKey: $NEWRELIC_LICENSE_KEY
      rbac.create: true
```

## Istio

```
istio:
    version: "0.8.0"
    repository:
      git: git@github.com:istio/istio.git
      path: install/kubernetes/helm
    namespace: istio-system
    values:
      global:
        nodePort: true
        hub: docker.io/istio
        tag: 0.8.0
        namespace: istio-system
        mtls:
          enabled: true
      prometheus.enabled: true
      grafana.enabled: true
      tracing:
        enabled: false
        jaeger:
          enabled: true
        ingress:
          enabled: false
        service:
          type: ClusterIP
      ingress:
        service.type: NodePort
        autoscaleMin: 1
        autoscaleMax: 3
        resources:
          limits:
           cpu: 50m
           memory: 64Mi
          requests:
           cpu: 10m
           memory: 32Mi
      ingressgateway:
        service.type: NodePort
        autoscaleMin: 1
        autoscaleMax: 6
        resources:
          limits:
           cpu: 50m
           memory: 64Mi
          requests:
           cpu: 10m
           memory: 32Mi
      egressgateway:
        autoscaleMin: 1
        autoscaleMax: 3
        resources:
          limits:
           cpu: 50m
           memory: 64Mi
          requests:
           cpu: 10m
           memory: 32Mi
```
