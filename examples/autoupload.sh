#!/bin/bash

RUNS_DIR="2014-15.timetable.cam.ac.uk-runs"
TTUSER="someusername"
TTPASSWORD="notherealpassword"

# Change into the script's dir
cd "$( dirname "${BASH_SOURCE[0]}")"

# Create the dir that run logs will be stored in
mkdir -p "$RUNS_DIR"

autoimport_outfile=$(mktemp)

# Run the autoimport
TTPW="$TTPASSWORD" ttapiutils autoimport engineering -X tripos=engineering -X substitutions=substitutions.json -X exclusions=exclusions-2014-15.json -X year=2014 -X part=IA -X part=IB -X part=IIA -X part=IIB 2014-15.timetable.cam.ac.uk /tripos/engineering/{I,II}{A,B} --audit-trail $RUNS_DIR --user $TTUSER --pass-envar TTPW --dry-run &> "$autoimport_outfile" &

autoimport_pid=$!
wait $autoimport_pid
autoimport_status=$?

echo "autoimport: pid: $autoimport_pid, status: $autoimport_status"

if [ $autoimport_status -ne 0 ] ; then
	logger -t autoimport-engineering -p user.error -s  "Timetable Engineering autoimport (pid:$autoimport_pid) failed, status:$autoimport_status" "$(cat $autoimport_outfile)"
else
	logger -t autoimport-engineering -p user.info -s "Timetable Engineering autoimport (pid:$autoimport_pid) succeeded."
fi

rm "$autoimport_outfile"
exit $autoimport_status
