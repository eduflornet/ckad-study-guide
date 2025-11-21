# Mock Scenario 6: Namespace Isolation

**Scenario:**
Two teams, `team-x` and `team-y`, have their own namespaces. Ensure that pods in `team-x` cannot communicate with pods in `team-y` using NetworkPolicy.

**Requirements:**
- NetworkPolicy to block cross-namespace traffic
- Namespaces: team-x, team-y

**Questions:**
1. Write the YAML manifest for the isolation policy.
2. How do you verify that isolation is enforced?
3. What command lists all pods in both namespaces?

**Expected Outcome:**
- Pods in `team-x` and `team-y` are fully isolated from each other.