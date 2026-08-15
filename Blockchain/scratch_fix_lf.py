import os

files_to_fix = [
    'fabric-network/deploy-backup-gce.sh',
    'fabric-network/deploy-chaincode.sh',
    'fabric-network/scripts/deploy-chaincode.sh'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"Fixing line endings for {file_path}...")
        with open(file_path, 'rb') as f:
            content = f.read()
        # Replace CRLF with LF
        fixed_content = content.replace(b'\r\n', b'\n')
        with open(file_path, 'wb') as f:
            f.write(fixed_content)
    else:
        print(f"File not found: {file_path}")

print("Line endings fix completed!")
