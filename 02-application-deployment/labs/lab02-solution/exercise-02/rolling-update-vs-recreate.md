**Rolling update**
How it works: Gradually replaces old pods with new ones, often in small batches. New pods are started before old ones are terminated, so the application remains available throughout the update.
Downtime: Minimal to none.
Risk: If the new version has a critical bug, it can be propagated across many pods.
When to use: For applications requiring high availability and continuous service.

**Recreate**
How it works: Shuts down all existing pods and then starts the new ones.
Downtime: A complete, but often short, downtime period occurs while the old pods are down and the new ones are starting up.
Risk: If the new version fails, the application is completely unavailable until a fix is deployed.
When to use: When downtime is acceptable, such as during development or for applications that can tolerate a brief outage.

