#!/bin/bash
COLLECTION="postman/LegalQA_Integration.postman_collection.json"
ENVIRONMENT="postman/dev_environment.json"

newman run $COLLECTION -e $ENVIRONMENT \
  -r cli,html --reporter-html-export newman_report.html
