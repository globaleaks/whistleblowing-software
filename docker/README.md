# GlobaLeaks Docker Image (experimental)

## With Docker CLI

Build the image with:

    docker build -t globaleaks/globaleaks .

Run the built image with:

    docker run --rm -it -p '80:80' -p '443:443' globaleaks/globaleaks

## With docker-compose

Build and run with:

    docker-compose up --build

## Access

Go to http://localhost and follow the setup wizard.
