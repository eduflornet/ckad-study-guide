# Mock Scenario 4: TLS Ingress

**Scenario:**
You need to secure access to a service named `secure-app` in the `prod` namespace using TLS termination at the Ingress. The hostname should be `secure.local` and the TLS secret is named `secure-tls`.

**Requirements:**
- Ingress resource with TLS configuration
- Host: secure.local
- TLS secret: secure-tls
- Service: secure-app
- Namespace: prod

**Questions:**
1. Write the YAML manifest for the Ingress resource with TLS.
2. How do you create the TLS secret?
3. What command verifies the TLS configuration?

**Expected Outcome:**
- HTTPS requests to `secure.local` are routed to `secure-app`.