# Injector E2E CI (forks only)

Tests the Injector injection mode end to end with the **unreleased** add-on: the helm chart and the operator
come from fork branches, the Python SDK image from a fork branch, and the Injector `.so` from the development
release `aws-otel-injector-v0.11.0` on `wangzlei/aws-otel-python-instrumentation`. It is only needed until
add-on release 1; after that the test cases move to the official CI.

## Workflows

| Workflow | What it does |
|---|---|
| `injector-e2e.yml` (manual) | Orchestrates one run: build images (or reuse a previous `image-tag`), then the Python EKS validation with injection mode `old`, then with the Injector mode (both must pass: telemetry unchanged), then the start-up guard cases. Serialized per cluster (`concurrency`). Inputs: `ecr-repository`, `image-tag`, `arch` (amd64/arm64), `injection-mode`, chart repo/ref, operator and SDK refs, region, cluster. |
| `injector-ci-build-images.yml` | Builds and pushes multi-arch images to one ECR repository: operator (`wangzlei/amazon-cloudwatch-agent-operator@injector-mode`), Python SDK (`wangzlei/aws-otel-python-instrumentation@startup-guard`, Injector from the fork release), Python sample apps, traffic generator, guard test apps (`sample-apps/python/injector-guard`). Tags: `<repo>:<kind>-<tag>`. |
| `python-eks-injector-test.yml` | `python-eks-test.yml` adapted: add-on installed from the chart source with the operator image and `manager.instrumentationInjectionMode`; Python SDK image patched in; one role ARN; sample-app images as inputs; pods pinned to `arch`; checks `LD_PRELOAD` is set (Injector mode) or absent (old mode). Logs, metrics and traces are validated with the framework's validator. |
| `injector-guard-cases.yml` | UMG app (Python 3.9, urllib3 1.26.20) must become Ready after ≤ 3 restarts with `ADOT SDK skipped for python` and serve with its own urllib3; healthy app (Python 3.11) must run with the SDK and 0 restarts. |

The enablement scripts come from `wangzlei/application-signals-demo@injector-mode`, whose
`install-addon-via-helm.sh` accepts `HELM_CHART_REPO` and `INSTRUMENTATION_INJECTION_MODE`.

## AWS resources the CI needs (account 292779133546) — NOT created yet

| Resource | Why | Replaces in the team setup | How |
|---|---|---|---|
| GitHub OIDC provider `token.actions.githubusercontent.com` | keyless auth from GitHub Actions | team roles in secrets `APPLICATION_SIGNALS_E2E_TEST_*` | `oidc-role.cfn.yaml` (or reuse an existing provider via `ExistingOidcProviderArn`) |
| IAM role `injector-ci-github-actions`, trust `repo:wangzlei/*` only | all workflow AWS calls | same | `oidc-role.cfn.yaml`, policy = `iam-policy.json` |
| EKS access entry for that role (cluster admin, cluster scope) | `helm install` of the add-on creates cluster-scoped objects | team cluster access | `oidc-role.cfn.yaml` (`CreateClusterAccessEntry`); needs cluster authentication mode `API` or `API_AND_CONFIG_MAP`; deploy the stack in the cluster's region |
| GitHub secret `INJECTOR_CI_ROLE_ARN` on `wangzlei/aws-application-signals-test-framework` | the role ARN | `APPLICATION_SIGNALS_E2E_TEST_ACCOUNT_ID` / `_ROLE_NAME` | `gh secret set INJECTOR_CI_ROLE_ARN -R wangzlei/aws-application-signals-test-framework` |
| EKS cluster `guard-test` (us-east-2), existing | runs the tests | team test clusters | must **not** have the managed add-on `amazon-cloudwatch-observability` installed (the CI installs the chart with helm); needs an IAM OIDC provider for IRSA associated once (`eksctl utils associate-iam-oidc-provider`; the CI role can only read it); x86 node group (`ng`, exists) and an ARM node group for `arch=arm64` (to be added) |
| ECR repository `guard-test` (us-west-2), existing | all test images | team ECR (`e2e-test/python-*-sample-app-image`, `e2e-test-resource:traffic-generator`) | node role must be able to pull (AmazonEC2ContainerRegistryReadOnly) |
| Application Signals service-linked role | required by Application Signals | same | created by `enable-app-signals.sh` on the first run (allowed by the policy) |
| IRSA roles `eks-s3-access-<id>` and `eksctl-guard-test-addon-iamserviceaccount-*` | sample app S3 access; CloudWatch agent | same | created and deleted per run by eksctl (allowed by the policy, attachments limited to the 3 managed policies used) |
| Terraform state | — | — | none: the `terraform/python/eks` module uses local state |

## Before the first run

1. Deploy `oidc-role.cfn.yaml` in us-east-2 (after review) and set the `INJECTOR_CI_ROLE_ARN` secret.
2. On `guard-test`: remove the managed add-on, associate the IAM OIDC provider if missing, add the ARM node group.
3. `workflow_dispatch` only lists workflows that exist on the repository's default branch: put branch
   `injector-mode` on the fork's default branch (or make `injector-mode` the default branch of the fork).
4. Run: `gh workflow run injector-e2e.yml -R wangzlei/aws-application-signals-test-framework -f ecr-repository=292779133546.dkr.ecr.us-west-2.amazonaws.com/guard-test`
   (add `-f arch=arm64` for ARM; add `-f image-tag=<run id of an earlier build>` to skip building).
