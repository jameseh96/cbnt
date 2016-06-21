if lnt create /lnt/db/db ; then
    echo "No existing database found, new one created.\n"
else
    echo "Existing database found, not creating new one. If you wish to create a new database please delete existing database on the host and re-run container.\n"
fi

lnt runserver /lnt/db/db --hostname=0.0.0.0