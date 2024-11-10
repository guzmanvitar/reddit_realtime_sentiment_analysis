# Real Time Sentiment Analysis on the X platform
## 1. Getting started with the repo

### Installing virtual environments and getting dependencies

1. **Poetry**

Before we start to code, we need to set up a virtual environment to handle the project dependencies separately
from our system's Python packages. This will ensure that whatever we run on our local machine will be
reproducible in any teammate's machine.

I use `poetry` to to install and manage dependencies. I also use `pyenv` (see [here](https://github.com/pyenv/pyenv-installer)) to manage python versions.

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

1. **Docker & Kubernetes**

Going one step further from poetry lock files, we want to have our code containerized to really ensure a deterministic
build, no matter where we execute. This repo uses docker to containerize the code and kubernetes to orechestrate containers.

To locally test the kubernetes cluster you can install `minikube` (see [here](https://minikube.sigs.k8s.io/docs/start/)).

Custom images used in yamls in kubernetes are stored in my personal GCP Container Registry. You can either ping me for
credentials or build the images from the Dockerfiles, push to your own CR and modify the kubernetes yamls accordingly.

To login to docker using gcp credentials run:
```bash
    cat .secrets/gcp_service_account_creds.json | docker login -u _json_key --password-stdin https://gcr.io
```

To use the credentials in kubernetes run:
```bash
    kubectl create secret docker-registry gcr-json-key --docker-server=gcr.io --docker-username=_json_key --docker-password="$(cat .secrets/gcp_service_account_creds.json)" --docker-email=any@valid.email
```

You can check everything is working as its supposed to by running the postgres db and local python env deployments:
```bash
    kubectl apply -f postgres-db.yaml
    kubectl apply -f kubernetes/python-env.yaml
```

The python-env containers are installed wth the latest poetry lock available in this repo. Anything you can run locally you should
be able to run inside these containers. To access the containers you can kubectl exec into the corresponding pod and container, or
you can access the jupyter lab at:
```bash
minikube service python-env --url
```

Whatever the method, once inside the container try for one simple test:
```bash
python src/db_scripts/test_database_connection.py
```
