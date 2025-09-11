#!/bin/bash
set -e # Stop if errors happen

echo 'Testing API'

response_1=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/retrieve \
     -o temp_response.json \
     -H "Content-type:application/json" \
     -d '{"question":"What is Chapter I Article 1 of Civil Law?","top_k":5}')

http_code_1=$(tail -n1 <<< "$response_1")
if [ "$http_code_1" = "200" ]; then
    echo "API /retrieve successful!"
    cat temp_response.json
else
    echo -e "\nAPI /retrieve error, response code: $http_code_1"
    exit 1
fi

response_2=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/rag \
     -o temp_response.json \
     -H "Content-type:application/json" \
     -d '{"question":"What is Chapter I Article 1 of Civil Law?"}')

http_code_2=$(tail -n1 <<< "$response_2")
if [ "$http_code_2" = "200" ]; then
    echo -e "\nAPI /rag successful!"
    cat temp_response.json
else
    echo -e "\nAPI /rag error, response code: $http_code_2"
    exit 2
fi

# Clean up temp file
rm -f temp_response.json

echo -e "\nAll smoke tests completed successfully!"
