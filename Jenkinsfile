#!/usr/bin/env groovy
@Library('lib')_
 
pythonPipeline {
  package_name = "openeo-cdse-benchmarks"
  test_module_name = "."
  wipeout_workspace = true
  python_version = ["3.10"]
  run_tests = false
  build_wheel = false
  upload_dev_wheels = false
  pep440 = true
  extra_env_variables = [
    "OPENEO_AUTH_METHOD=client_credentials",
    "OPENEO_OIDC_DEVICE_CODE_MAX_POLL_TIME=5",
    "OPENEO_AUTH_PROVIDER_ID=CDSE",
    "OPENEO_AUTH_CLIENT_ID=openeo-cdse-ci-service-account",
  ]
  extra_env_secrets = [
    'OPENEO_AUTH_CLIENT_SECRET': 'TAP/big_data_services/openeo/cdse-service-accounts/openeo-cdse-ci-service-account client_secret',
  ]
}
