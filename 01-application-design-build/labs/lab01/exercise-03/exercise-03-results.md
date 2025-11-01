
### Compare Image Sizes

```bash
# Build both versions
docker build -f Dockerfile.bad -t app-bad .
docker build -f Dockerfile.good -t app-good .

# Compare sizes
docker images | grep app-

python-app-good   latest    98a0d8ac0ead   2 minutes ago   74.8MB
app-bad           latest    92f2f8ebcb0e   6 minutes ago   548MB

```

