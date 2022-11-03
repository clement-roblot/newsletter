#!/bin/bash

srcDir=`pwd`
cd `pipenv --venv`/lib/python*/site-packages
zip -r $srcDir/deploymentPackage.zip .
cd $srcDir
zip -gr deploymentPackage.zip *
aws lambda update-function-code --function-name mailingList --zip-fil fileb://deploymentPackage.zip
