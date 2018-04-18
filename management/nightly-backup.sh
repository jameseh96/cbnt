#!/usr/bin/env bash

last_error=0

function fatal_error_handler() {
    last_error=$?
    echo "Fatal error - aborting"
    exit $last_error
}

timestamp() {
  date +"%m.%d.%y-%T"
}

trap fatal_error_handler ERR

cd ../..
mkdir -p cbnt_data_backups
sudo tar czfv cbnt_data_backups/backup-$(timestamp).tar cbnt_data/