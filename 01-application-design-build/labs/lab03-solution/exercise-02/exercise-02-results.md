docker build -f Dockerfile.patched -t secure-app .
[+] Building 1.1s (12/12) FINISHED                                                                                    docker:default
 => [internal] load build definition from Dockerfile.patched                                                                    0.0s
 => => transferring dockerfile: 478B                                                                                            0.0s
 => [internal] load metadata for docker.io/library/python:3.11-alpine                                                           0.9s
 => [internal] load .dockerignore                                                                                               0.0s
 => => transferring context: 2B                                                                                                 0.0s
 => [1/7] FROM docker.io/library/python:3.11-alpine@sha256:610ede222c1fa9675c694c99429f8d2c1b4e243f1982246da9e540eb5800ee4a     0.0s
 => [internal] load build context                                                                                               0.0s
 => => transferring context: 203B                                                                                               0.0s
 => CACHED [2/7] RUN apk add --no-cache     curl     openssl                                                                    0.0s
 => CACHED [3/7] RUN adduser -D appuser                                                                                         0.0s
 => CACHED [4/7] WORKDIR /app                                                                                                   0.0s
 => CACHED [5/7] COPY requirements.txt .                                                                                        0.0s
 => CACHED [6/7] RUN pip install --no-cache-dir -r requirements.txt                                                             0.0s
 => CACHED [7/7] COPY --chown=appuser:appuser app.py .                                                                          0.0s
 => exporting to image                                                                                                          0.0s
 => => exporting layers                                                                                                         0.0s
 => => writing image sha256:4cd29aa1bb5b0c28db157c578139da8f5ed893d78f93606cc423e0bb3ee8d089                                    0.0s
 => => naming to docker.io/library/secure-app                                                                                   0.0s
 echo "=== VULNERABLE APP ===" && $HOME/.local/bin/trivy image vulnerable-app --severity HIGH,CRITICAL --quiet
=== VULNERABLE APP ===

Report Summary

┌──────────────────────────────────────────────────────────────────────────────┬────────────┬─────────────────┬─────────┐
│                                    Target                                    │    Type    │ Vulnerabilities │ Secrets │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ vulnerable-app (ubuntu 22.04)                                                │   ubuntu   │        3        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/Flask-1.0.dist-info/METADATA          │ python-pkg │        1        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/certifi-2025.10.5.dist-info/METADATA  │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/chardet-3.0.4.dist-info/METADATA      │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/click-8.3.0.dist-info/METADATA        │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/idna-2.7.dist-info/METADATA           │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/itsdangerous-2.2.0.dist-info/METADATA │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/jinja2-3.1.6.dist-info/METADATA       │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/markupsafe-3.0.3.dist-info/METADATA   │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/requests-2.20.0.dist-info/METADATA    │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/urllib3-1.24.3.dist-info/METADATA     │ python-pkg │        1        │    -    │
├──────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.10/dist-packages/werkzeug-3.1.3.dist-info/METADATA     │ python-pkg │        0        │    -    │
└──────────────────────────────────────────────────────────────────────────────┴────────────┴─────────────────┴─────────┘
Legend:
- '-': Not scanned
- '0': Clean (no security findings detected)


vulnerable-app (ubuntu 22.04)

Total: 3 (HIGH: 3, CRITICAL: 0)

┌────────────────┬────────────────┬──────────┬──────────┬───────────────────┬───────────────┬─────────────────────────────────────────────────────────┐
│    Library     │ Vulnerability  │ Severity │  Status  │ Installed Version │ Fixed Version │                          Title                          │
├────────────────┼────────────────┼──────────┼──────────┼───────────────────┼───────────────┼─────────────────────────────────────────────────────────┤
│ linux-libc-dev │ CVE-2024-35870 │ HIGH     │ affected │ 5.15.0-161.171    │               │ kernel: smb: client: fix UAF in smb2_reconnect_server() │
│                │                │          │          │                   │               │ https://avd.aquasec.com/nvd/cve-2024-35870              │
│                ├────────────────┤          │          │                   ├───────────────┼─────────────────────────────────────────────────────────┤
│                │ CVE-2024-53179 │          │          │                   │               │ kernel: smb: client: fix use-after-free of signing key  │
│                │                │          │          │                   │               │ https://avd.aquasec.com/nvd/cve-2024-53179              │
│                ├────────────────┤          │          │                   ├───────────────┼─────────────────────────────────────────────────────────┤
│                │ CVE-2025-38118 │          │          │                   │               │ kernel: Bluetooth: MGMT: Fix UAF on                     │
│                │                │          │          │                   │               │ mgmt_remove_adv_monitor_complete                        │
│                │                │          │          │                   │               │ https://avd.aquasec.com/nvd/cve-2025-38118              │
└────────────────┴────────────────┴──────────┴──────────┴───────────────────┴───────────────┴─────────────────────────────────────────────────────────┘

Python (python-pkg)

Total: 2 (HIGH: 2, CRITICAL: 0)

┌────────────────────┬────────────────┬──────────┬────────┬───────────────────┬────────────────┬─────────────────────────────────────────────────────────────┐
│      Library       │ Vulnerability  │ Severity │ Status │ Installed Version │ Fixed Version  │                            Title                            │
├────────────────────┼────────────────┼──────────┼────────┼───────────────────┼────────────────┼─────────────────────────────────────────────────────────────┤
│ Flask (METADATA)   │ CVE-2023-30861 │ HIGH     │ fixed  │ 1.0               │ 2.3.2, 2.2.5   │ flask: Possible disclosure of permanent session cookie due  │
│                    │                │          │        │                   │                │ to missing Vary: Cookie...                                  │
│                    │                │          │        │                   │                │ https://avd.aquasec.com/nvd/cve-2023-30861                  │
├────────────────────┼────────────────┤          │        ├───────────────────┼────────────────┼─────────────────────────────────────────────────────────────┤
│ urllib3 (METADATA) │ CVE-2023-43804 │          │        │ 1.24.3            │ 2.0.6, 1.26.17 │ python-urllib3: Cookie request header isn't stripped during │
│                    │                │          │        │                   │                │ cross-origin redirects                                      │
│                    │                │          │        │                   │                │ https://avd.aquasec.com/nvd/cve-2023-43804                  │
└────────────────────┴────────────────┴──────────┴────────┴───────────────────┴────────────────┴─────────────────────────────────────────────────────────────┘
 echo "=== SECURE APP ===" && $HOME/.local/bin/trivy image secure-app --severity HIGH,CRITICAL --quiet
=== SECURE APP ===

Report Summary

┌──────────────────────────────────────────────────────────────────────────────────┬────────────┬─────────────────┬─────────┐
│                                      Target                                      │    Type    │ Vulnerabilities │ Secrets │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ secure-app (alpine 3.22.2)                                                       │   alpine   │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/blinker-1.9.0.dist-info/METADATA          │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/click-8.3.0.dist-info/METADATA            │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/flask-2.3.3.dist-info/METADATA            │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/itsdangerous-2.2.0.dist-info/METADATA     │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/jinja2-3.1.6.dist-info/METADATA           │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/markupsafe-3.0.3.dist-info/METADATA       │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/pip-24.0.dist-info/METADATA               │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools-79.0.1.dist-info/METADATA      │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/autocommand-2.2.2.dis- │ python-pkg │        0        │    -    │
│ t-info/METADATA                                                                  │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/backports.tarfile-1.2- │ python-pkg │        0        │    -    │
│ .0.dist-info/METADATA                                                            │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/importlib_metadata-8.- │ python-pkg │        0        │    -    │
│ 0.0.dist-info/METADATA                                                           │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/inflect-7.3.1.dist-in- │ python-pkg │        0        │    -    │
│ fo/METADATA                                                                      │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/jaraco.collections-5.- │ python-pkg │        0        │    -    │
│ 1.0.dist-info/METADATA                                                           │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/jaraco.context-5.3.0.- │ python-pkg │        0        │    -    │
│ dist-info/METADATA                                                               │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/jaraco.functools-4.0.- │ python-pkg │        0        │    -    │
│ 1.dist-info/METADATA                                                             │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/jaraco.text-3.12.1.di- │ python-pkg │        0        │    -    │
│ st-info/METADATA                                                                 │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/more_itertools-10.3.0- │ python-pkg │        0        │    -    │
│ .dist-info/METADATA                                                              │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/packaging-24.2.dist-i- │ python-pkg │        0        │    -    │
│ nfo/METADATA                                                                     │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/platformdirs-4.2.2.di- │ python-pkg │        0        │    -    │
│ st-info/METADATA                                                                 │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/tomli-2.0.1.dist-info- │ python-pkg │        0        │    -    │
│ /METADATA                                                                        │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/typeguard-4.3.0.dist-- │ python-pkg │        0        │    -    │
│ info/METADATA                                                                    │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/typing_extensions-4.1- │ python-pkg │        0        │    -    │
│ 2.2.dist-info/METADATA                                                           │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/wheel-0.45.1.dist-inf- │ python-pkg │        0        │    -    │
│ o/METADATA                                                                       │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/setuptools/_vendor/zipp-3.19.2.dist-info- │ python-pkg │        0        │    -    │
│ /METADATA                                                                        │            │                 │         │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/werkzeug-3.1.3.dist-info/METADATA         │ python-pkg │        0        │    -    │
├──────────────────────────────────────────────────────────────────────────────────┼────────────┼─────────────────┼─────────┤
│ usr/local/lib/python3.11/site-packages/wheel-0.45.1.dist-info/METADATA           │ python-pkg │        0        │    -    │
└──────────────────────────────────────────────────────────────────────────────────┴────────────┴─────────────────┴─────────┘
Legend:
- '-': Not scanned
- '0': Clean (no security findings detected)

echo "=== IMAGE SIZE COMPARISON ===" && docker images | grep -E "(vulnerable-app|secure-app)"
=== IMAGE SIZE COMPARISON ===
vulnerable-app    latest     e9de72bf8997   2 minutes ago    506MB
secure-app        latest     4cd29aa1bb5b   15 minutes ago   75.6MB