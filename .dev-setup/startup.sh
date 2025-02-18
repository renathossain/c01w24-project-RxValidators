#!/bin/bash

type="$1"
if [ "$type" = "install" ]; then
    command="npm install"
else
    command="npm run $type"
fi

if [ -z "$type" ]; then
    command="npm run dev"
fi

# Need MongoDB Running
gnome-terminal --tab --title="MongoDB" --working-directory=$PWD -- /bin/bash -c "mongod --dbpath='data/db'; exec bash" &
until nc -z localhost 27017
do
    sleep 1
done
gnome-terminal --tab --title="API Gateway" --working-directory=$PWD/backend/api_gateway -- /bin/bash -c "$command; exec bash" &
until nc -z localhost 3130
do
    sleep 1
done
# gnome-terminal --tab --title="Auth Service" --working-directory=$PWD/backend/auth_service -- /bin/bash -c "$command; exec bash" &
gnome-terminal --tab --title="Verification Service" --working-directory=$PWD/backend/verification_service -- /bin/bash -c "python -m src.main.py; exec bash" &
gnome-terminal --tab --title="ScrapeDescription Service" --working-directory=$PWD/backend -- /bin/bash -c "source .venv/bin/activate; python scrapeDescription.py; exec bash" &
gnome-terminal --tab --title="Prescriber Service" --working-directory=$PWD/backend/database_functions -- /bin/bash -c "source .venv/bin/activate; python database_Prescriptions.py; exec bash" &
gnome-terminal --tab --title="Authentication Service" --working-directory=$PWD/backend/auth_service -- /bin/bash -c "source .venv/bin/activate; python database_Authentications.py; exec bash" &
gnome-terminal --tab --title="Frontend" --working-directory=$PWD/frontend -- /bin/bash -c "$command; exec bash" &
