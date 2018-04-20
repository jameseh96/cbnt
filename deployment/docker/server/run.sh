if lnt create /lnt/db/db; then
    echo "No existing database found, new one created.\n"
else
    echo "Existing database found, not creating new one. If you wish to create a new database please delete existing database on the host and re-run container.\n"
fi

cd /lnt/deployment
gunicorn app_wrapper:app -w 8 -b 0.0.0.0:8000 --max-requests 10 --timeout 300