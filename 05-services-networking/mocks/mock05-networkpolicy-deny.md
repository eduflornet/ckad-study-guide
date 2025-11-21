# Mock Scenario 5: Default Deny NetworkPolicy

**Scenario:**
A namespace `restricted` contains several pods. Implement a NetworkPolicy that denies all ingress and egress traffic by default. Only allow traffic from pods with the label `access: allowed`.

**Requirements:**
- NetworkPolicy with default deny
- Allow ingress from pods with label `access: allowed`
- Namespace: restricted

**Questions:**
1. Write the YAML manifest for the NetworkPolicy.
2. How do you test that traffic is denied?
3. What command lists all NetworkPolicies in the namespace?

**Expected Outcome:**
- Only pods with the correct label can communicate; all other traffic is blocked.