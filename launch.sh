#!/bin/bash

BASEDIR=$(dirname "$0")

cd $BASEDIR
/usr/bin/pipenv run ./sendInstance.py
