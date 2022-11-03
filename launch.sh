#!/bin/bash

BASEDIR=$(dirname "$0")

cd $BASEDIR
/usr/local/bin/pipenv run ./sendInstance.py
