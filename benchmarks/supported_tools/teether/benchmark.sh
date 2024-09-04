#!/bin/bash

# Directory containing the contracts
CONTRACT_DIR="contracts" 
RESULT_DIR="../results/teTher"

# Create result directory if it doesn't exist
mkdir -p "$RESULT_DIR "

# Iterate over each Solidity file in the contracts directory
for file in "$CONTRACT_DIR"/*.sol; do
  if [[ -f "$file" ]]; then
    # Extract the filename without extension
    filename=$(basename -- "$file")
    filename_no_ext="${filename%.*}"
    
    # Extract the pragma version from the Solidity file
    pragma_version=$(grep -oE 'pragma solidity \^[0-9]+\.[0-9]+\.[0-9]+' "$file" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')

    # Check if pragma version was found
    if [[ -n "$pragma_version" ]]; then
      # Install and use the extracted Solidity version
      solc-select install "$pragma_version"
      solc-select use "$pragma_version"

      # Generate the .code file
      solc --bin "$file" | tail -n1 > "$CONTRACT_DIR/$filename_no_ext.code"

      # Generate the .contract.code file
      python bin/extract_contract_code.py "$CONTRACT_DIR/$filename_no_ext.code" > "$CONTRACT_DIR/$filename_no_ext.contract.code"

      # Generate the exploit and store the output in the log file
      python bin/gen_exploit.py "$CONTRACT_DIR/$filename_no_ext.contract.code" 0x1234 0x1000 +1000 > "$RESULT_DIR/$filename_no_ext.log"
    else
      echo "No pragma version found in $file"
    fi
  else
    echo "No Solidity files found in $CONTRACT_DIR"
  fi
done
