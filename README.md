# Reddit Real Time Sentiment Analysis
## 1. Local development

### Installing virtual environments and getting dependencies

1. **Poetry**

This repo uses `poetry` to install and manage dependencies. We also use `pyenv` (see [here](https://github.com/pyenv/pyenv-installer)) to manage python versions.

The codebase uses `Python 3.11.10`. So after installing `pyenv` and `poetry` run
```bash
pyenv install 3.11.10
pyenv shell 3.11.10
pyenv which python | xargs poetry env use
poetry config virtualenvs.in-project true
poetry install
```
to create a virtual environment, and install all dependencies to it. Then, close the terminal and activate the `poetry` env with
```bash
    poetry shell
```
Once inside the shell we'll also run
```bash
    pre-commit install
```
to setup git hooks.

2. **Docker & Kubernetes**

For a fast local test of the code a docker-compose file is provided.
Just install [docker-compose](https://docs.docker.com/compose/install/), then run docker-compose up.

We'll use GCP's kubernetes cluster for production however, so to locally test the kubernetes deployment you can install
`minikube` (see [here](https://minikube.sigs.k8s.io/docs/start/)).

Custom images used in yamls in kubernetes are stored in my personal GCP Container Registry. You can either ping me for
credentials or build the images from the Dockerfiles, push to your own CR and modify the kubernetes yamls accordingly.

In any case, once you have you GCP credentials you'll need to store them under .secrets/gcp_service_account_creds.json

To login to docker using gcp credentials run:
```bash
    cat .secrets/gcp_service_account_creds.json | docker login -u _json_key --password-stdin https://southamerica-east1-docker.pkg.dev
```

To use the credentials in kubernetes run:
```bash
kubectl create secret docker-registry gcr-json-key \
--docker-server=southamerica-east1-docker.pkg.dev \
--docker-username=_json_key \
--docker-password="$(cat .secrets/gcp_service_account_creds.json)" \
--docker-email=any@valid.email
```

You can check everything is working as its supposed to by running the postgres db and local python env deployments:
```bash
    kubectl apply -f kubernetes/python-env.yaml
```

The python-env containers are installed wth the latest poetry lock available in this repo. Anything you can run locally you should
be able to run inside this dev container. To access the container you can kubectl exec into the corresponding pod and container, or
you can access the jupyter lab at:
```bash
minikube service python-env --url
```
