# Injector start-up guard test app

Used by `injector-guard-cases.yml`.

- `PYTHON_VERSION=3.9`: with ADOT Python v0.21.0 injected, the SDK's bundled urllib3 shadows the app's
  urllib3 1.26.20 and the app crashes at start-up. With the Injector start-up guard the pod must recover
  after a few restarts and serve without the SDK.
- `PYTHON_VERSION=3.11`: healthy app; must start with the SDK and 0 restarts.
