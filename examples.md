## course.yml config section
```
namespace: kube-system
repository: stable
repositories:
  incubator:
    url: https://kubernetes-charts-incubator.storage.googleapis.com
  stable:
    url: https://kubernetes-charts.storage.googleapis.com
minimum_versions: #set minimum version requirements here
  helm: 2.10.0
  reckoner: 0.6.3
charts:
```

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

This includes autodiscovery of instancegroups and the 'least-waste' expander option.

See the [Autoscaler Docs](https://github.com/helm/charts/tree/master/stable/cluster-autoscaler#auto-discovery) for details on how to tag your nodes and set permissions for this to work.

```
  cluster-autoscaler:
    repository: stable
    version: "0.7.0"
    values:
      cloudProvider: aws
      replicaCount: 2
      autoDiscovery.clusterName: cluster.example.com
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
      extraArgs.skip-nodes-with-local-storage\=false: ""
      extraArgs.skip-nodes-with-system-pods\=false: ""
      extraArgs.scan-interval: "30s"
      extraArgs.expander: "least-waste"
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
    version: "1.10.1"
    repository: stable
    values:
      daemonset:
        updateStrategy: RollingUpdate
        tolerations:
        - key: node-role.kubernetes.io/master
          effect: NoSchedule
      rbac.create: "true"
      kubeStateMetrics.enabled: "true"
      kube-state-metrics.rbac.create: "true"
      datadog:
        apiKey: "${DATADOG_API_KEY}"
        appKey: "${DATADOG_APP_KEY}"
        leaderElection: "true"
        collectEvents: "true"
        resources:
          requests:
            cpu: 100m
            memory: 250Mi
          limits:
            cpu: 200m
            memory: 500Mi
      clusterAgent:
        enabled: true
        token: "${DATADOG_CLUSTER_AGENT_TOKEN}"
        metricsProvider:
          enabled: true
```

Enable Statsd Collection in Datadog.  This will create a deployment with a service on port 8125/UDP that you can send statsd metrics to.

```
  datadog-statsd:
    chart: datadog
    version: 1.0.1
    repository: stable
    values:
      daemonset.enabled: "false"
      deployment.enabled: "true"
      daemonset.updateStrategy: RollingUpdate
      kubeStateMetrics.enabled: "false"
      datadog:
        apiKey: "${DATADOG_API_KEY}"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 200m
            memory: 256Mi
        volumeMounts:
          - name: confd
            mountPath: /etc/datadog-agent/datadog.yaml
            readOnly: true
            subPath: datadog.yaml
        confd:
          datadog\.yaml: |
            use_dogstatsd: true
            dogstatsd_port: 8125
            dogstatsd_non_local_traffic: true
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
```

## rbac-manager

```
  rbac-manager:
    repository:
      git: https://github.com/reactiveops/rbac-manager.git
    chart: chart
    version: 0.4.1
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
      controller.metrics.enabled: true
      controller.stats.enabled: true
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
    values-strings:
      controller.podAnnotations:
        ad\.datadoghq\.com/nginx-ingress-controller\.check_names: |
          ["prometheus"]
        ad\.datadoghq\.com/nginx-ingress-controller\.init_configs: |
          [{}]
        ad\.datadoghq\.com/nginx-ingress-controller\.instances: |
          [
            {
              "prometheus_url": "http://%%host%%:10254/metrics"\,
              "namespace": "ingress"\,
              "metrics": ["nginx*"\, "ingress*"]
            }
          ]
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
    version: "1.0.1"
    repository:
      git: git@github.com:istio/istio.git
      path: install/kubernetes/helm
    namespace: istio-system
    values:
      grafana:
        enabled: true
        security:
          enabled: true
          adminUser: admin
          adminPassword: "${GRAFANA_ADMIN_PASS}"
      tracing.enabled: true
      servicegraph.enabled: true
```

## Metrics Server

```
  metrics-server:
    version: "1.1.0"
```
