#!/bin/bash
set -xe

./script/authoring-assistant.sh config=$1
./script/generate-charts.sh $1
./script/generate-summary-table.sh $1
